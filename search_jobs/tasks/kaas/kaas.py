import logging, re
import numpy as np
from app.config.env import environment
from app.sql_app.dbenums.core_enums import PersonaEnum
from batch_jobs.enums.ingress_enums import IngestionSourceEnum, JobType
from batch_jobs.internal.scheduler.task import Task
import requests
import pandas as pd
from batch_jobs.tasks.utils.analytics import DataQualityProcessor
from batch_jobs.tasks.utils.utils import *
from app.config import app_config
import datetime
from opensearchpy import OpenSearch
from opensearchpy.helpers import bulk
from concurrent.futures import ThreadPoolExecutor, as_completed
from bs4 import BeautifulSoup

app_configs = app_config.AppConfig.get_all_configs()
phase1_index = app_config.AppConfig.get_sectionwise_configs("index_values")


class KaasAPI(Task):

    failed_records_df = pd.DataFrame(columns=["Record", "Error", "Source"])
    failed_products=[]

    def __init__(self, run_type: str, from_date = None):
        super().__init__("KaasTask")
        self.run_type = run_type
        self.custom_from_date = from_date
    def run(self):
        super().run()
        self.kaas_job()

    def make_api_request(self):
        # Get configuration

        access_token = kaas_access_token()

        # Define base parameters for API request
        base_params = {
            "resultLimit": "3000",
            "printFields": "documentID,title,contenttypeheader,product,contenttype,contentupdatedate,languagecode,disclosurelevel,store,description,renderlink,ishType,technicalLevel,productstagged,hpid",
        }
        if self.run_type == JobType.INCREMENTAL:
            # from_date = (datetime.datetime.now() - datetime.timedelta(days=6)).strftime("%Y-%m-%d")
            from_date = self.custom_from_date if self.custom_from_date else self.last_successful_run
            from_date = from_date.strftime("%Y-%m-%d")
            base_params["fromDate"] = from_date
            logging.info(f"Running incremental job from date: {from_date}")
        else:
            logging.info("Running historical job")
        df = pd.DataFrame()
        params_generator = create_params_kaas()

        def fetch_data(v1, v2):
            # Function to make a single API request
            params = base_params.copy()
            params['product'] = v1
            params['disclosureLevel'] = v2
            url = app_configs["kaas_api_base_url"]
            headers = {
                'Content-Type': 'application/json',
                'Authorization': 'Bearer ' + access_token,
            }
            try:
                response = requests.get(url, params=params, headers=headers)
                response.raise_for_status()
                data = response.json()
                return pd.DataFrame(data.get('matches', []))
            except requests.exceptions.HTTPError as e:
                return pd.DataFrame()  # Return an empty DataFrame if there's an error

        # Use ThreadPoolExecutor to run requests in parallel
        with ThreadPoolExecutor(max_workers=50) as executor:
            futures = [executor.submit(fetch_data, v1, v2) for v1, v2 in params_generator]
            for future in as_completed(futures):
                df1 = future.result()
                df = pd.concat([df, df1])

        df = df.drop_duplicates(subset='documentID', keep='last')
        return df

    def preprocess_data(self, df):
        if df.empty:
            print("DataFrame is empty. Skipping preprocessing.")
            return df  # Return the empty DataFrame immediately

        try:
            # Get lookup data from configuration
            config = KaasAPIConfig()
            lookup = config.getlookup()

            parent_doc_mapping_path = app_configs["parent_doc_mapping_path"]

            parent_doc_mapping = pd.read_csv(parent_doc_mapping_path)

            # Merge main DataFrame with parentDoc mapping
            df = pd.merge(
                df,
                parent_doc_mapping,
                how="left",
                left_on="documentID",
                right_on="documentID",
            )
            df["description"] = df["description"].apply(
                lambda x: BeautifulSoup(x, "lxml")
                .get_text(separator="\n")
                .strip()
                .replace("\n", " ")
            )
            # Combine title and description columns
            df["ti_desc_prod"] = (
                df["title"].fillna("")
                + " "
                + df["description"].fillna("")
                + " "
                + df["documentID"].fillna("")
            )

            df["ti_desc_prod"] = df["ti_desc_prod"].replace(r"^\s*$", "N/A", regex=True)

            # Create Doc_status field
            df["Doc_Status"] = df["ti_desc_prod"].apply(
                lambda x: "rejected" if x == "N/A" else "published"
            )
            df["Domain"] = df["products"].apply(
                lambda products: (
                    set(
                        filter(
                            None,
                            (
                                config.get_domain_for_product(product_id)
                                for product_id in products
                            ),
                        )
                    )
                    if products
                    else None
                )
            )
            df["Domain"] = df["Domain"].apply(
                lambda x: ", ".join(x) if isinstance(x, set) else ""
            )

            mask = df["Domain"] == ""
            # Apply the domain extraction logic only to the filtered rows
            df.loc[mask, "Domain"] = np.where(
                df.loc[mask, "ti_desc_prod"].str.contains("Indigo", case=False),
                "Indigo",
                np.where(
                    df.loc[mask, "ti_desc_prod"].str.contains("PageWide", case=False),
                    "PWP",
                    "",
                ),
            )

            # Map product IDs to product names
            df["product_info"] = df.apply(
                lambda row: [
                    lookup[str(id)] for id in row["products"] if str(id) in lookup
                ],
                axis=1,
            )

            # Map disclosureLevel to persona
            persona_map = {
                "287477763180518087286275037723076": PersonaEnum.Operator.value,
                "47406819852170807613486806879990": PersonaEnum.Engineer.value,
                "696531864679532034919979251200881": PersonaEnum.Operator.value,
                "600096605536507071488362545356335": PersonaEnum.Engineer.value,
                "218620138892645155286800249901443": PersonaEnum.Operator.value,
                "887243771386204747508092376253257": PersonaEnum.Engineer.value,
            }

            df["persona"] = df["disclosureLevel"].replace(persona_map)

            df["renderLink"] = df["renderLink"].apply(
                lambda x: x if isinstance(x, str) and len(x) < 100 else None
            )

            # Drop unnecessary columns
            df.drop(columns=["products", "topIssue"], inplace=True)

            language_code_mapping = language_lookup()

            # Strip whitespace and normalize case
            df["language"] = df["language"].str.strip().str.title()

            # Replace the language names with their corresponding ISO codes
            df["language"] = df["language"].replace(language_code_mapping)
            # Rename column
            df.rename(
                columns={"Pdfs": "parentDoc", "product_info": "products"}, inplace=True
            )

            df["parentDoc"] = df["parentDoc"].replace("N/A", "")
            df.fillna("", inplace=True)

            df["parentDoc"] = df["parentDoc"].replace(r"^\s*$", None, regex=True)
            df["renderLink"] = df["renderLink"].replace(r"^\s*$", None, regex=True)

            df["products"] = df["products"].apply(
                lambda x: list(set(x)) if x not in [None, ""] else []
            )

            df.loc[
                df["ti_desc_prod"].str.contains("Coca-Cola", case=False, na=False),
                "Doc_Status",
            ] = "rejected"

            df["renderLink"] = df["renderLink"].apply(
                lambda x: x if isinstance(x, str) and len(x) < 100 else None
            )

            df = df[~(df["contentUpdateDate"].eq("") | df["contentUpdateDate"].isna())]

            return df
        except Exception as e:
            logging.error("An error occurred during preprocessing: %s", str(e))
            raise

    def index_data_to_opensearch(self, df, index_name):
        # Connect to OpenSearch

        timeout_seconds = app_configs["timeout_seconds"]
        client = OpenSearch(
            hosts=[{"host": app_configs["host"], "port": app_configs["port"]}],
            http_compress=True,
            http_auth=(
                app_configs["opensearch_auth_user"],
                environment.AUTH_OPENSEARCH_PASSWORD,
            ),
            use_ssl=app_configs["use_ssl"],
            verify_certs=app_configs["verify_certs"],
            timeout=int(timeout_seconds),
        )

        dict_list = df.to_dict(orient="records")
        document_ids = [record["documentID"] for record in dict_list]

        # Batch fetch existing documents
        existing_docs = fetch_existing_documents(client, index_name, document_ids)

        # Initialize counters and lists
        successful_records = 0
        failed_records = []
        new_records = 0
        updated_records = 0

        # Prepare actions for bulk indexing with upsert
        actions = []
        for record in dict_list:
            if existing_docs.get(record["documentID"], False):
                updated_records += 1
            else:
                new_records += 1

            action = {
                "_index": index_name,
                "_id": record["documentID"],
                "pipeline": app_configs["emb_pipeline"],
                "_op_type": "update",
                "doc": record,
                "doc_as_upsert": True,
            }
            actions.append(action)

        # Perform bulk indexing with upsert
        try:
            success, _ = bulk(client, actions=actions)
            successful_records = success
        except Exception as e:
            # Log and store failed records
            for record in dict_list:
                failed_records.append((record, str(e), "KAAS_API"))
                logging.error(
                    f"Failed to index document {record}: {e}  : 'KAAS_API_INGRESS'"
                )
        # Store failed records and update fromDate if necessary
        if failed_records:
            logging.info(
                f"Indexing completed with {len(failed_records)} failed records."
            )
            self.store_failed_records(failed_records)
        else:
            # Update fromDate attribute if all records are successful
            current_datetime = datetime.datetime.now()
            KaasAPI.fromDate = current_datetime.strftime("%Y-%m-%d")
            logging.info("All records indexed successfully. Updating fromDate.")

        # Log indexing statistics to 'kas_log_index' index
        try:
            data_to_index = {
                "successful_records": successful_records,
                "failed_records": len(failed_records),
                "new_records": new_records,
                "updated_records": updated_records,
                "timestamp": datetime.datetime.now(),
                "Source": IngestionSourceEnum.KAAS_API_DATA_INGESTION.value,
                "index_loaded": index_name,
            }
            client.index(
                index=app_configs["kaas_ingestion_log_index"], body=data_to_index
            )
            logging.info("Successfully indexed data to kas_log_index.")
        except Exception as e:
            logging.error(f"Failed to index data to kas_log_index: {e}")
        logging.info(
            "successful_records: %s ::: failed_records: %s",
            successful_records,
            failed_records,
        )

        return successful_records, len(failed_records)

    def store_failed_records(self, failed_records):
        try:
            # Check if the DataFrame is empty
            if len(KaasAPI.failed_records_df) == 0:
                # Initialize failed_records_df if it's empty
                KaasAPI.failed_records_df = pd.DataFrame(
                    columns=["Record", "Error", "Source"]
                )

            # Convert failed_records to DataFrame
            failed_records_df_new = pd.DataFrame(
                failed_records, columns=["Record", "Error", "Source"]
            )

            # Concatenate new records with existing DataFrame
            KaasAPI.failed_records_df = pd.concat(
                [KaasAPI.failed_records_df, failed_records_df_new], ignore_index=True
            )

            # Log success message
            logging.info(
                f"Failed records stored successfully. Total failed records: {len(KaasAPI.failed_records_df)}"
            )

            # Return updated DataFrame
            return KaasAPI.failed_records_df
        except Exception as e:
            # Log error if storing failed records fails
            logging.error(f"Failed to store failed records: {e}")
            return None

    def kaas_job(self):

        df = self.make_api_request()

        if df.shape[0] == 0:
            print("No recent data available. Exiting job.")
            return {"status": "No data", "message": "API returned no recent data"}

        df1 = self.preprocess_data(df)
        if df1.shape[0] == 0:
            print("No recent data available. Exiting job.")
            return {"status": "No data", "message": "API returned no recent data"}
        qc_df = DataQualityProcessor.process_dataframe(
            df1, phase1_index["kaas"], False, False
        )
        qc_data_log = DataQualityProcessor.generate_qc_data_log(
            qc_df, phase1_index["kaas"]
        )

        DataQualityProcessor.index_data_to_opensearch(
            qc_df,
            app_configs["ingress_analytics_visualization_index"],
            qc_data_log,
        )

        result = self.index_data_to_opensearch(df1, index_name=phase1_index["kaas"])
        return result
