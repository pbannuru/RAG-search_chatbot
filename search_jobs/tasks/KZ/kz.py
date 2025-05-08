import ast
import logging, re
import os
from app.config.env import environment
from app.sql_app.dbenums.core_enums import DomainEnum, PersonaEnum
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


class KZLoader(Task):
    failed_records_df = pd.DataFrame(columns=["Record", "Error", "Source"])

    def __init__(self, run_type: str, from_date=None):
        super().__init__("KZTask")
        self.run_type = run_type
        self.custom_from_date = from_date

    def run(self):
        super().run()
        self.kz_job()

    def make_api_request(self):
        headers = kz_create_headers()
        proxies = None

        # Determine if running locally or on server
        if environment.KZ_USE_PROXY:
            proxies = {app_configs["proxy_request_type"]: app_configs["proxy_url"]}

        base_url = app_configs["kz_api_base_url"]
        params = {
            "size": 250,
            "date": "01/01/2010 00:00:00",
            "from": 0,
        }

        if self.run_type == JobType.INCREMENTAL:
            # from_date = (datetime.datetime.now() - datetime.timedelta(days=3)).strftime("%d/%m/%Y %H:%M:%S")
            from_date = self.custom_from_date if self.custom_from_date else self.last_successful_run
            from_date = from_date.strftime("%d/%m/%Y %H:%M:%S")
            # from_date = (
            #     self.last_successful_run - datetime.timedelta(days=6)
            # ).strftime("%d/%m/%Y %H:%M:%S")
            # print(f"Adjusted from_date (6 days earlier): {from_date}")
            # print(from_date)
            params["date"] = from_date
            logging.info(f"Running incremental job from date: {from_date}")
        else:
            logging.info("Running historical job")

        # Initial request to get the total number of records
        initial_response = requests.get(
            base_url, headers=headers, proxies=proxies, params=params
        )
        initial_data = initial_response.json()
        total_records = initial_data["kzOfflineAssetList"]["total"]
        all_data = initial_data["kzOfflineAssetList"]["members"]

        def fetch_data(start):
            batch_params = params.copy()
            batch_params["from"] = start
            response = requests.get(
                base_url, headers=headers, proxies=proxies, params=batch_params
            )
            response.raise_for_status()
            return response.json()["kzOfflineAssetList"]["members"]

        with ThreadPoolExecutor(max_workers=10) as executor:
            futures = [
                executor.submit(fetch_data, start)
                for start in range(params["size"], total_records, params["size"])
            ]
            for future in as_completed(futures):
                all_data.extend(future.result())

        df = pd.json_normalize(all_data, sep="_")
        df.columns = [col.replace("assetResponse_", "") for col in df.columns]

        return df

    def preprocess_data(self, df):
        if df.empty:
            print("DataFrame is empty. Skipping preprocessing.")
            return df  # Return the empty DataFrame immediately

        # Create the 'asset_state' column
        df["asset_state"] = df.apply(
            lambda row: {
                "name": row["asset_state_name"],
                "numericOrder": row["asset_state_numericOrder"],
                "dueDate": row["asset_state_dueDate"],
            },
            axis=1,
        )

        # Create the 'publisher' column
        df["publisher"] = df.apply(
            lambda row: {"id": row["publisher_id"], "name": row["publisher_name"]},
            axis=1,
        )

        # Create the 'ratingResponse' column
        df["ratingResponse"] = df.apply(
            lambda row: {
                "number_of_votes": row["ratingResponse_number_of_votes"],
                "rating": row["ratingResponse_rating"],
            },
            axis=1,
        )

        # lambda Function to extract first names from tag group
        product_to_device = kz_get_pwp_device_lookup()

        df["products"] = df["tags_groups"].apply(
            lambda tag_groups: (
                [
                    {"name": tag["name"].strip(), "type": tag["type"].strip()}
                    for group in tag_groups
                    for tag in group["tags_names"]
                ]
                if isinstance(tag_groups, list)
                else []
            )
        )

        df["products"] = df["products"].apply(
            lambda products: [
                p["name"]
                for p in products
                if p["type"]
                in ["Press Model", "Press Series", "Platforms", "3D Printing Series"]
            ]
        )

        df["products"] = df["products"].apply(
            lambda products_list: [
                item
                for product in products_list
                for item in product_to_device.get(product, [product])
            ]
        )
        df["products"] = df["products"].apply(lambda x: list(set(x)))

        df.loc[
            (df["bu"] == DomainEnum.PWP.name) & (df["tags_groups"].isna()), "products"
        ] = df.loc[
            (df["bu"] == DomainEnum.PWP.name) & (df["tags_groups"].isna()), "products"
        ].apply(
            lambda x: x + ["PWP-Generic"] if isinstance(x, list) else ["PWP-Generic"]
        )

        # Filter the DataFrame (if needed)
        df = df[df["bu"].isin(["Indigo", "Pwi", "PWP",'ThreeD'])].copy()
        df["bu"] = df["bu"].replace("Pwi", "scitex")
        # Rename columns
        df.rename(
            columns={
                "id": "documentID",
                "bu": "Domain",
                "body": "description",
                "name": "title",
                "fileType": "contentType",
                "modification_date": "contentUpdateDate",
                "lowestRoles_lowestRole_roleName": "lowestRolesList",
            },
            inplace=True,
        )

        df["persona"] = df["lowestRolesList"].apply(
            lambda role: (
                "Operator"
                if role in ["Press Operator", "PSP Admin"]
                else (
                    "Engineer"
                    if role in ["HP CE", "Channel", "KZ Admin"]
                    else "NOROLES"
                )
            )
        )

        # Drop the original separate columns
        columns_to_drop = [
            "actionEnum",
            "created_by",
            "notification_date",
            "size",
            "upload_date",
            "asset_state_name",
            "header",
            "tags_groups",
            "projectID",
            "keyWordResponses",
            "isIndexable",
            "isVisible",
            "isActive",
            "notificationProperties_isFilteredByDeviceType",
            "asset_state_numericOrder",
            "ratingResponse_rating",
            "asset_state_dueDate",
            "lowestRoles_lowestRole_id",
            "lowestRoles_lowestRolesSet",
            "lowestRoles_lowestRole_name",
            "lowestRoles_lowestRole_level",
            "lowestRoles_lowestRole_bu",
            "publisher_id",
            "publisher_name",
            "ratingResponse_number_of_votes",
            "notificationProperties_isRealTimeNotification",
            "notificationProperties_isWeeklyReport",
            "roles",
            "thumbnail_url",
            "lowestRolesSet",
            "original_name",
        ]
        df.drop(
            columns=[col for col in columns_to_drop if col in df.columns], inplace=True
        )

        language_code_mapping = language_lookup()

        # Strip whitespace and normalize case
        df["language"] = df["language"].str.strip().str.title()

        # Replace the language names with their corresponding ISO codes
        df["language"] = df["language"].replace(language_code_mapping)

        df["language"] = df["language"].str.lower()

        df["contentUpdateDate"] = pd.to_datetime(df["contentUpdateDate"]).dt.strftime(
            "%Y-%m-%d %H:%M:%S"
        )

        kz_render_url = app_configs["kz_render_url"]
        # Create the 'url' column
        df["renderLink"] = df["documentID"].apply(lambda x: f"{kz_render_url}/{x}")

        # Fill NaN values
        df.fillna("", inplace=True)
        df["description"] = df.apply(
            lambda row: (
                row["description"] + " " + str(row["catalog_number"])
                if str(row["catalog_number"]) not in row["description"]
                else row["description"]
            ),
            axis=1,
        )

        df["description"] = df["description"].apply(
            lambda x: BeautifulSoup(x, "lxml")
            .get_text(separator="\n")
            .strip()
            .replace("\n", " ")
        )

        df["ti_desc_prod"] = df["title"].fillna("") + " " + df["description"].fillna("")
        df["ti_desc_prod"] = df["ti_desc_prod"].replace(r"^\s*$", "N/A", regex=True)
        df["ti_desc_prod"] = df["ti_desc_prod"].apply(lambda x: re.sub(r"<.*?>", "", x))

        df["Doc_Status"] = df.apply(
            lambda x: (
                "rejected"
                if x["ti_desc_prod"] == "N/A" or x["persona"] == "NOROLES"
                else "published"
            ),
            axis=1,
        )
        # c500_records = df[
        #     df["products"].apply(lambda x: any("C5" in i.upper() for i in x))
        # ]["documentID"]
        # df = df[~df["documentID"].isin(c500_records)]

        pwp_cat_path_kz = app_configs["pwp_cat_path_kz"]

        pwp_e = pd.read_csv(pwp_cat_path_kz)

        pwp_e["documentID"] = pwp_e["documentID"].astype(int)
        df = pd.merge(
            df, pwp_e, how="left", left_on="documentID", right_on="documentID"
        )
        df["products_new"] = df["products_new"].apply(
            lambda x: (
                ast.literal_eval(x) if isinstance(x, str) and x.strip() != "" else []
            )
        )
        condition = df["products"].apply(lambda x: len(x) < 1)
        # Replace values in 'products' with corresponding values from 'products_new' where the condition is True
        df.loc[condition, "products"] = df.loc[condition, "products_new"]

        df.loc[
            df["Category"].notna() & (df["Category"] != "Press Platform"),
            "ti_desc_prod",
        ] += (
            " - " + df["Category"]
        )

        df.drop(columns=["Category", "products_new", "Press Platform"], inplace=True)

        indigo_prod_map_kz = app_configs["indigo_prod_map_kz"]

        indigo_pr = pd.read_csv(indigo_prod_map_kz)

        indigo_mapping_dict = pd.Series(
            indigo_pr["products"].values, index=indigo_pr["catalog_number"]
        ).to_dict()

        df["catalog_number"] = df["catalog_number"].str.strip().str.upper()

        df["catalog_number"].apply(lambda x: indigo_mapping_dict.get(x))

        df.loc[
            (df["products"].apply(lambda x: len(x) < 1)) & (df["Domain"] == "Indigo"),
            "products",
        ] = df["catalog_number"].apply(lambda x: indigo_mapping_dict.get(x, []))
        df.loc[
            (df["products"].apply(lambda x: len(x) < 1))
            & (df["Doc_Status"] == "published"),
            "products",
        ] = df.loc[
            (df["products"].apply(lambda x: len(x) < 1))
            & (df["Doc_Status"] == "published"),
            "ti_desc_prod",
        ].apply(
            lambda x: find_all_devices(x)
        )

        df["products"] = df["products"].apply(
            lambda x: (
                x
                if isinstance(x, list)
                else (ast.literal_eval(x) if isinstance(x, str) else [x])
            )
        )

        df['documentID'] = df['documentID'].astype('str')
        
        df.loc[
            df["ti_desc_prod"].str.contains("Coca-Cola", case=False, na=False),
            "Doc_Status",
        ] = "rejected"

        df['assetGroup'] = df['assetGroup'].astype('str')
        # Step 1: Extract parent records
        parent_df = df[df['documentID'] == df['assetGroup']][['assetGroup', 'persona', 'Doc_Status', 'products']]
        
        parent_df = parent_df.rename(columns={
            'persona': 'persona_parent',
            'Doc_Status': 'Doc_Status_parent',
            'products': 'products_parent'
        })
        
        # Step 2: Merge parent info back into full df using assetGroup
        df = df.merge(parent_df, on='assetGroup', how='left')
        
        #Step 3: Replace child values with parent values only when needed
        df['persona'] = df.apply(lambda row: row['persona_parent'] if row['persona'] == 'NOROLES' else row['persona'], axis=1)
        df['Doc_Status'] = df.apply(lambda row: row['Doc_Status_parent'] if row['Doc_Status'] == 'rejected' else row['Doc_Status'], axis=1)
        df['products'] = df.apply(lambda row: row['products_parent'] if row['products'] == [] else row['products'], axis=1)
        
        #Step 4: Drop the temporary parent columns
        df = df.drop(columns=['persona_parent', 'Doc_Status_parent', 'products_parent'])
        return df

    def index_data_to_opensearch(self, df, index_name):
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
                failed_records.append((record, str(e), "kzloader_API"))
                logging.error(f"Failed to prepare document {record}: {e}")

        if failed_records:
            logging.info(
                f"Indexing completed with {len(failed_records)} failed records."
            )
            self.store_failed_records(failed_records)

        try:
            data_to_index = {
                "successful_records": successful_records,
                "failed_records": len(failed_records),
                "new_records": new_records,
                "updated_records": updated_records,
                "timestamp": datetime.datetime.now(),
                "Source": "kzloader_DATA_INGESTION",
                "index_loaded": index_name,
            }
            client.index(
                index=app_configs["kz_ingestion_log_index"], body=data_to_index
            )

            logging.info("Successfully indexed data to kzloader_log_index.")
        except Exception as e:
            logging.error(f"Failed to index data to kzloader_log_index: {e}")

        logging.info(
            "successful_records: %s ::: failed_records: %s",
            successful_records,
            failed_records,
        )
        return successful_records, len(failed_records)

    def store_failed_records(self, failed_records):
        try:
            if len(KZLoader.failed_records_df) == 0:
                KZLoader.failed_records_df = pd.DataFrame(
                    columns=["Record", "Error", "Source"]
                )

            failed_records_df_new = pd.DataFrame(
                failed_records, columns=["Record", "Error", "Source"]
            )
            KZLoader.failed_records_df = pd.concat(
                [KZLoader.failed_records_df, failed_records_df_new], ignore_index=True
            )

            logging.info(
                f"Failed records stored successfully. Total failed records: {len(KZLoader.failed_records_df)}"
            )
            return KZLoader.failed_records_df
        except Exception as e:
            logging.error(f"Failed to store failed records: {e}")
            raise

    def kz_job(self):

        df = self.make_api_request()

        if df.shape[0] == 0:
            print("No recent data available. Exiting job.")
            return {"status": "No data", "message": "API returned no recent data"}
        df1 = self.preprocess_data(df)
        if df1.shape[0] == 0:
            print("No recent data available. Exiting job.")
            return {"status": "No data", "message": "API returned no recent data"}
        qc_df = DataQualityProcessor.process_dataframe(
            df1, phase1_index["kz"], False, True
        )
        qc_data_log = DataQualityProcessor.generate_qc_data_log(
            qc_df, phase1_index["kz"]
        )
        DataQualityProcessor.index_data_to_opensearch(
            qc_df,
            app_configs["ingress_analytics_visualization_index"],
            qc_data_log,
        )
        result = self.index_data_to_opensearch(df1, phase1_index["kz"])
        return result
