import ast
import re
from opensearchpy import OpenSearch
from opensearchpy.helpers import bulk
from app.config.env import environment
from app.sql_app.dbenums.core_enums import DomainEnum
from batch_jobs.enums.ingress_enums import IngestionSourceEnum, JobType
from batch_jobs.internal.scheduler.task import Task
from batch_jobs.tasks.utils.analytics import DataQualityProcessor
from batch_jobs.tasks.utils.utils import *
import logging
from app.config import app_config
import requests
import pandas as pd
import datetime
import concurrent.futures
from concurrent.futures import ThreadPoolExecutor, as_completed
from bs4 import BeautifulSoup

app_configs = app_config.AppConfig.get_all_configs()
phase1_index = app_config.AppConfig.get_sectionwise_configs('index_values')


class DoceboCourseDeltaLoader(Task):
    failed_records_df = pd.DataFrame(columns=["Record", "Error", "Source"])

    def __init__(self, run_type: str,from_date=None):
        super().__init__("DocceboCourseIngressTask")
        self.run_type = run_type
        self.custom_from_date = from_date

    def run(self):
        super().run()
        self.doccebo_course_delta_job()

    def fetch_doccebo_course_data(self):
        # Define API endpoint URL
        base_url = app_configs["doccebo_course_delta_url"]
        # Define parameters (filters)
        params = {
            "page_size": 10,
            "adv": "1",
        }
        if self.run_type == JobType.INCREMENTAL:
            # from_date = (datetime.datetime.now() - datetime.timedelta(days=3)).strftime("%Y-%m-%d %H:%M:%S")
            from_date = self.custom_from_date if self.custom_from_date else self.last_successful_run
            # from_date = self.last_successful_run
            params["updated_from"] = from_date
            logging.info(f"Running incremental job from date: {from_date}")
        else:
            logging.info("Running historical job")

        docebo_bearer = get_doccebo_access_token()

        # Make initial request to determine total pages
        initial_response = requests.get(
            base_url,
            params=params,
            headers={"Authorization": "Bearer " + docebo_bearer},
        )
        initial_response.raise_for_status()
        initial_data = initial_response.json()
        total_pages = initial_data["data"]["total_page_count"]
        data = initial_data["data"]["items"]  # Collect the initial page

        def fetch_page_data(page):
            """Fetch a single page of Docebo course data."""
            page_params = params.copy()
            page_params["page"] = page
            response = requests.get(
                base_url,
                params=page_params,
                headers={"Authorization": "Bearer " + docebo_bearer},
            )
            response.raise_for_status()
            return response.json()["data"]["items"]

        # Use ThreadPoolExecutor to fetch multiple pages in parallel
        with ThreadPoolExecutor(max_workers=10) as executor:
            futures = [
                executor.submit(fetch_page_data, page)
                for page in range(2, total_pages + 1)
            ]
            for future in as_completed(futures):
                data.extend(future.result())
        return data

    def preprocessing(self, data):
        """
        This function preprocesses course data for further analysis.
        It performs the following operations:
        1. Converts input data to a DataFrame.
        2. Renames specific columns for consistency.
        3. Drops unnecessary columns.
        4. Fills missing values in certain columns.
        5. Combines the title and description into a single column.
        6. Assigns a domain based on the code and filters the DataFrame.
        7. Assigns personas based on patterns in the slug name.
        8. Merges with an external product mapping DataFrame.
        9. Fills any remaining missing values with empty strings.
        """
        df = pd.DataFrame(data)
        if df.empty:
            print("DataFrame is empty. Skipping preprocessing.")
            return df  # Return the empty DataFrame immediately
        try:

            # Rename columns for consistency
            updated_columns = {
                "id_course": "documentID",
                "name": "title",
                "uidCourse": "id",
                "date_last_updated": "contentUpdateDate",
                "course_type": "contentType",
            }
            df.rename(columns=updated_columns, inplace=True)

            # Drop unnecessary columns if they exist in the DataFrame
            columns_to_drop = [
                "start_date",
                "end_date",
                "duration",
                "available_seats",
                "available_seats_course",
            ]
            columns_to_drop = [col for col in columns_to_drop if col in df.columns]
            df.drop(columns=columns_to_drop, inplace=True)

            # Fill missing values in specific columns with -1
            columns_to_fill = ["current_rating", "max_attempts"]
            df[columns_to_fill] = df[columns_to_fill].fillna(-1)

            df["description"] = df["description"].apply(
                lambda x: BeautifulSoup(x, "lxml")
                .get_text(separator="\n")
                .strip()
                .replace("\n", " ")
            )
            # Combine title and description into a single column
            df["ti_desc_prod"] = (
                df["title"].fillna("") + " " + df["description"].fillna("")
            )
            df["ti_desc_prod"] = df["ti_desc_prod"].replace(r"^\s*$", "N/A", regex=True)

            # Create Doc_status field
            df["Doc_Status"] = df["ti_desc_prod"].apply(
                lambda x: "rejected" if x == "N/A" else "published"
            )

            df.loc[(df['code'].apply(lambda x:'gsb.s' in x)),'Domain']='scitex'

            scitex_df = df[df['Domain']=='scitex']
            # Mark the domain as 'Indigo' if the code contains the search string
            indigo_search_string = "gsb.i"
            df.loc[df["code"].str.contains(indigo_search_string), "Domain"] = (
                DomainEnum.Indigo.name
            )

            pwp_search_string = "gsb.pwp"

            df.loc[df["code"].str.contains(pwp_search_string), "Domain"] = (
                DomainEnum.PWP.name
            )

            # Filter rows where Domain is 'Indigo' or  'pwp'
            df = df[df["Domain"].isin([DomainEnum.Indigo.name, DomainEnum.PWP.name, DomainEnum.Scitex.value])]

            language_code_mapping = language_lookup()

            # Strip whitespace and normalize case
            df["language"] = df["language"].str.strip().str.title()

            # Replace the language names with their corresponding ISO codes
            df["language"] = df["language"].replace(language_code_mapping)

            indigo_category_path = app_configs["indigo_category_path"]
            pwp_category_path = app_configs["pwp_category_path"]

            indigo_df = pd.read_csv(indigo_category_path)
            pwp_df = pd.read_csv(pwp_category_path)

            indigo_service_category = indigo_df["indigo_category"].tolist()
            pwp_category = pwp_df["pwp_category"].tolist()

            indigo_df = df[df["Domain"] == DomainEnum.Indigo.name].loc[
                lambda x: x["category"].apply(
                    lambda y: y["id"] in indigo_service_category
                )
            ]

            pwp_df = df[df["Domain"] == DomainEnum.PWP.name].loc[
                lambda x: x["category"].apply(lambda y: y["id"] in pwp_category)
            ]
            # pwp_df = df[df['Domain']=='PWP']
            df = pd.concat([indigo_df, pwp_df, scitex_df], ignore_index=True)

            df['products'] = [[] for _ in range(len(df))]
            # Fill any remaining missing values with empty strings
            docebo_render_url = app_configs["docebo_render_url"]
            df["renderLink"] = df["documentID"].apply(
                lambda x: f"{docebo_render_url}/{x}"
            )

            patterns = [
                r"^(HP Indigo.*?(Press(?:es)?|Series))",
                r"^(HP PWP.*?(Series|T\d+))",
            ]

            df.fillna("", inplace=True)
            df["products"] = df["products"].apply(lambda x: [] if x == "" else x)
            df.loc[df["products"].apply(lambda x: len(x) < 1), "products"] = df[
                "ti_desc_prod"
            ].apply(lambda x: find_all_devices(x))
            df["products"] = df.apply(
                lambda row: (
                    row["products"]
                    if row["products"] not in [None, []]
                    else [
                        match.group(0)
                        for pattern in patterns
                        if (match := re.search(pattern, row["title"], re.IGNORECASE))
                        and len(match.group(0).split()) < 7
                    ]
                ),
                axis=1,
            )
            df["products"] = df["products"].apply(
                lambda lst: (
                    [
                        f"{' '.join(parts[:2])} {model} {parts[-1]}"
                        for device in lst
                        if isinstance(device, str)
                        for parts in [device.split(" ")]
                        if len(parts) >= 3 and "/" in parts[2]
                        for model in parts[2].split("/")
                    ]
                    + [
                        device
                        for device in lst
                        if isinstance(device, str) and "/" not in device
                    ]
                    if isinstance(lst, list)
                    else lst
                )
            )
            df["products"] = df["products"].apply(
                lambda devices_list: (
                    [
                        device.strip()
                        for item in devices_list
                        for device in item.split(",")
                    ]
                    if all(isinstance(item, str) for item in devices_list)
                    else devices_list
                )
            )

            df.loc[df["products"].apply(lambda x: len(x) < 1), "products"] = df[
                "category"
            ].apply(lambda x: find_all_devices(x["name"]))

            cat_device_path = app_configs["cat_device_path"]

            cat_df = pd.read_csv(cat_device_path)

            cat_df["products"] = cat_df["products"].apply(ast.literal_eval)
            cat_map = dict(zip(cat_df["categories"], cat_df["products"]))
            df.loc[df["products"].apply(lambda x: len(x) < 1), "products"] = df.loc[
                df["products"].apply(lambda x: len(x) < 1), "category"
            ].apply(lambda x: cat_map.get(x["name"].strip(), []))

            df["products"] = df["products"].apply(
                lambda x: (
                    x
                    if isinstance(x, list)
                    else (ast.literal_eval(x) if isinstance(x, str) else [x])
                )
            )

            condition = (
                (df['products'].apply(lambda x: len(x) == 0)) &
                (df['Domain'] == 'Indigo') &
                (df['category'].apply(lambda x: 'general' in x.get('name', '').lower() or 'HP Indigo Digital Press' in x.get('name', '')))
            )
            
            # Apply the condition and update the 'products' column
            df.loc[condition, 'products'] = df.loc[condition, 'products'].apply(lambda x: ['HP Indigo Digital Press'])
            
            category_to_products = {
                'HP PageWide C500 Press Training': ['HP PageWide C500 Press'],
                'HP Scitex 11000 Industrial Press': ['HP Scitex 11000 Industrial Press'],
                'HP Scitex 17000 Corrugated Press': ['HP Scitex 17000 Corrugated Press'],
                'FB500/700': ['FB500', 'FB700']
            }
            
            # Apply mapping only to relevant rows
            df.loc[df['category'].apply(lambda x: x.get('name') in category_to_products), 'products'] = \
                df['category'].apply(lambda x: category_to_products.get(x.get('name'), x))

            df.loc[df['ti_desc_prod'].str.contains('Coca-Cola', case=False, na=False), 'Doc_Status'] = 'rejected'
            
            df.loc[df['code'].str.contains('archived', case=False), 'Doc_Status'] = 'rejected'

            return df
        except Exception as e:
            logging.error("An error occurred during preprocessing: %s", str(e))
            return []

    def get_persona(self, df):

        course_ids = df["documentID"].tolist()
        attendee = {}
        docebo_bearer = get_doccebo_access_token()

        # Function to make the API request and process the response for each course
        def fetch_course_data(i):

            base_url = app_configs["doccebo_course_delta_url"]
            api_endpoint = f"{base_url}/{i}"
            headers = {"Authorization": "Bearer " + docebo_bearer}

            response = requests.get(api_endpoint, headers=headers)

            if response.status_code == 200:
                response_json = response.json()
                data = response_json["data"].get("additional_fields", [])
                is_published = response_json["data"].get("is_published", "N/A")
                press_name_dict = next(
                    (item for item in data if item["title"] == "Attendee Type"), None
                )

                if press_name_dict:
                    return i, {
                        "title": press_name_dict.get("title", "N/A"),
                        "value": press_name_dict.get("value", "N/A"),
                        "is_published": is_published,
                    }
                else:
                    print(
                        f"Course ID: {i} - 'Attendee Type' not found in additional fields"
                    )
                    return i, {"title": "Attendee Type", "value": "N/A"}
            else:
                print(
                    f"Course ID: {i} - Request failed with status code {response.status_code}"
                )
                return i, {"title": "Attendee Type", "value": "N/A"}

        # Parallel processing using ThreadPoolExecutor
        with concurrent.futures.ThreadPoolExecutor(max_workers=25) as executor:
            futures = {
                executor.submit(fetch_course_data, course_id): course_id
                for course_id in course_ids
            }

            for future in concurrent.futures.as_completed(futures):
                course_id, result = future.result()
                attendee[course_id] = result

        # Creating a DataFrame with results
        attendee_df = pd.DataFrame(
            [
                (k, v["value"], v.get("is_published", "N/A"))
                for k, v in attendee.items()
            ],
            columns=["documentID", "attendee_type", "is_published"],
        )
        updated_df = pd.merge(
            df, attendee_df, how="left", left_on="documentID", right_on="documentID"
        )
        updated_df["persona"] = updated_df["attendee_type"].apply(
            lambda x: (
                "Engineer"
                if x == "HP Employee / Staff"
                else "Operator" if x == "Customer" else "No_roles"
            )
        )
        updated_df["persona"] = updated_df.apply(
            lambda row: (
                "Engineer"
                if row["persona"] == "No_roles"
                and (
                    re.search(r"(\bce\b|\b-fse\b|\bce\b)", row["slug_name"].lower())
                    or "service-engineer" in row["slug_name"].lower()
                )
                else "Operator" if row["persona"] == "No_roles" else row["persona"]
            ),
            axis=1,
        )
        updated_df = updated_df[updated_df["is_published"] == True]
        updated_df['documentID']=updated_df['documentID'].astype('str')
        return updated_df

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
        document_ids = [record["id"] for record in dict_list]

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
            if existing_docs.get(record["id"], False):
                updated_records += 1
            else:
                new_records += 1

            action = {
                "_index": index_name,
                "_id": record["id"],
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
            failed_records.append((record, str(e), "'DOCCEBO_COURSE_DELTA_API'"))
            logging.error(
                f"Failed to index document {record}: {e}  : ''DOCCEBO_COURSE_DELTA_API'_INGRESS'"
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
            DoceboCourseDeltaLoader.fromDate = current_datetime.strftime("%Y-%m-%d")
            logging.info("All records indexed successfully. Updating fromDate.")

        # Log indexing statistics to 'doccebo_course_delta_log_index' index
        try:
            data_to_index = {
                "successful_records": successful_records,
                "failed_records": len(failed_records),
                "new_records": new_records,
                "updated_records": updated_records,
                "timestamp": datetime.datetime.now(),
                "Source": "DOCCEBO_API_COURSE_DATA_INGESTION",
                "index_loaded": index_name,
            }
            client.index(
                index=app_configs["docebo_ingestion_log_index"], body=data_to_index
            )
            logging.info("Successfully indexed data to doccebo_course_delta_log_index.")
        except Exception as e:
            logging.error(
                f"Failed to index data to doccebo_course_delta_log_index: {e}"
            )
        logging.info(
            "successful_records: %s ::: failed_records: %s",
            successful_records,
            failed_records,
        )
        return successful_records, len(failed_records)

    def store_failed_records(self, failed_records):
        try:
            # Check if the DataFrame is empty
            if len(DoceboCourseDeltaLoader.failed_records_df) == 0:
                # Initialize failed_records_df if it's empty
                DoceboCourseDeltaLoader.failed_records_df = pd.DataFrame(
                    columns=["Record", "Error", "Source"]
                )

            # Convert failed_records to DataFrame
            failed_records_df_new = pd.DataFrame(
                failed_records, columns=["Record", "Error", "Source"]
            )

            # Concatenate new records with existing DataFrame
            DoceboCourseDeltaLoader.failed_records_df = pd.concat(
                [DoceboCourseDeltaLoader.failed_records_df, failed_records_df_new],
                ignore_index=True,
            )

            # Log success message
            logging.info(
                f"Failed records stored successfully. Total failed records: {len(DoceboCourseDeltaLoader.failed_records_df)}"
            )

            # Return updated DataFrame
            return DoceboCourseDeltaLoader.failed_records_df
        except Exception as e:
            # Log error if storing failed records fails
            logging.error(f"Failed to store failed records: {e}")
            return None

    def doccebo_course_delta_job(self):

        data = self.fetch_doccebo_course_data()
        
        if not data:
            print("No recent data available. Exiting job.")
            return {"status": "No data", "message": "API returned no recent data"}
        

        df = self.preprocessing(data)
        df1 = self.get_persona(df)
        if df1.shape[0] == 0:
            print("No recent data available. Exiting job.")
            return {"status": "No data", "message": "API returned no recent data"}
        qc_df = DataQualityProcessor.process_dataframe(
            df1,  phase1_index["docebo"], True, False
        )
        qc_data_log = DataQualityProcessor.generate_qc_data_log(
            qc_df,  phase1_index["docebo"]
        )

        DataQualityProcessor.index_data_to_opensearch(
            qc_df,
            app_configs["ingress_analytics_visualization_index"],
            qc_data_log,
            include_id=True,
        )
        result = self.index_data_to_opensearch(df1,  phase1_index["docebo"])
        return result
