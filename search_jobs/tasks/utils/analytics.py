import datetime
from opensearchpy import OpenSearch
from opensearchpy.helpers import bulk
import pandas as pd
from app.config import app_config
from app.config.env import environment

app_configs = app_config.AppConfig.get_all_configs()


class DataQualityProcessor:

    @staticmethod
    def get_value(row, column):
        """Helper method to safely get a value from a row, returning an empty string if the column is missing."""
        return row[column] if column in row else ""

    @staticmethod
    def generate_remarks(row, include_id=False, include_catalog_number=False):
        remarks = {
            "documentID": DataQualityProcessor.get_value(row, "documentID"),
            "title": DataQualityProcessor.get_value(row, "title"),
            "products": DataQualityProcessor.get_value(row, "products"),
            "persona": DataQualityProcessor.get_value(row, "persona"),
            "description": DataQualityProcessor.get_value(row, "description"),
            "contentUpdateDate": DataQualityProcessor.get_value(
                row, "contentUpdateDate"
            ),
            "Domain": DataQualityProcessor.get_value(row, "Domain"),
            "Doc_Status": DataQualityProcessor.get_value(row, "Doc_Status"),
            "language": DataQualityProcessor.get_value(row, "language"),
            "Title_is_too_short": "NO",
            "Description_is_too_short": "NO",
            "Domain_is_empty": "NO",
            "Title_is_empty": "NO",
            "Description_is_empty": "NO",
            "Disclosure_Level_is_empty": "NO",
            "Persona_is_empty": "NO",
            "Products_is_empty": "NO",
            "catalog_number_is_empty": "NO",
        }

        # Assign 'id' based on include_id flag
        remarks["id"] = (
            DataQualityProcessor.get_value(row, "id") if include_id else None
        )

        # Assign 'catalog_number' based on include_catalog_number flag
        remarks["catalog_number"] = (
            DataQualityProcessor.get_value(row, "catalog_number")
            if include_catalog_number
            else None
        )

        # Check if catalog_number is empty
        if "catalog_number" in row and row["catalog_number"] == "":
            remarks["catalog_number_is_empty"] = "YES"

        if len(remarks["title"]) < 15 and len(remarks["title"]) > 0:
            remarks["Title_is_too_short"] = "YES"

        if len(remarks["description"]) < 30 and len(remarks["description"]) > 0:
            remarks["Description_is_too_short"] = "YES"

        if remarks["Domain"] == "":
            remarks["Domain_is_empty"] = "YES"

        if remarks["title"] == "":
            remarks["Title_is_empty"] = "YES"

        if remarks["description"] == "":
            remarks["Description_is_empty"] = "YES"

        if "disclosureLevel" in row and row["disclosureLevel"] == "":
            remarks["Disclosure_Level_is_empty"] = "YES"

        if "persona" in row and row["persona"] in ["", "NOROLES"]:
            remarks["Persona_is_empty"] = "YES"

        if "products" in row and (row["products"] is None or len(row["products"]) == 0):
            remarks["Products_is_empty"] = "YES"

        return remarks

    @staticmethod
    def process_dataframe(df, index_name, include_id, include_catalog_number):

        remarks_info = df.apply(
            DataQualityProcessor.generate_remarks,
            axis=1,
            include_id=include_id,
            include_catalog_number=include_catalog_number,
        )
        df_remarks = pd.DataFrame(remarks_info.tolist())
        df_remarks["Index_Name"] = index_name
        df_remarks["Source"] = index_name.split(".")[0]
        df_remarks['contentUpdateDate'] = pd.to_datetime(df_remarks['contentUpdateDate']).dt.strftime('%Y-%m-%d %H:%M:%S')
        df_remarks.fillna("", inplace=True)
        df_remarks["Contents"] = df_remarks.apply(
            lambda row: {
                "title": row["title"],
                "products": row["products"],
                "persona": row["persona"],
                "description": row["description"],
                "contentUpdateDate": row["contentUpdateDate"],
                "Domain": row["Domain"],
            },
            axis=1,
        )
        df_remarks["Contents"] = df_remarks["Contents"].apply(lambda x: str(x))
        df_remarks = df_remarks.drop(columns=["persona"])
        columns_to_check = [
            "Title_is_too_short",
            "Description_is_too_short",
            "Domain_is_empty",
            "Title_is_empty",
            "Description_is_empty",
            "Disclosure_Level_is_empty",
            "Persona_is_empty",
            "Products_is_empty",
        ]
        if index_name.split(".")[0] == "kz":
            columns_to_check.append("catalog_number_is_empty")

        # Create the 'issues' column
        df_remarks["contains_issue"] = df_remarks[columns_to_check].apply(
            lambda row: "YES" if "YES" in row.values else "NO", axis=1
        )

        if "kaas" in index_name:
            mask = df_remarks["documentID"].str.contains("ish") & (
                df_remarks["Title_is_too_short"] == "YES"
            )
            # Update the 'Title_is_too_short' column to 'N' for the filtered records
            df_remarks.loc[mask, "Title_is_too_short"] = "NO"

        return df_remarks

    @staticmethod
    def generate_qc_data_log(test_df, index_name):
        index_name = index_name
        columns_to_check = [
            "Title_is_too_short",
            "Description_is_too_short",
            "Domain_is_empty",
            "Title_is_empty",
            "Description_is_empty",
            "Disclosure_Level_is_empty",
            "Persona_is_empty",
            "Products_is_empty",
            "contains_issue",
        ]

        # Append 'catalog_number_is_empty' if index_name starts with 'kz'
        if index_name.startswith("kz"):
            columns_to_check.append("catalog_number_is_empty")

        # Create dictionary to store counts using lambda
        count_dict = {
            col: test_df[col].value_counts().get("YES", 0)
            for col in columns_to_check
            if col in test_df.columns
        }

        date_time = datetime.datetime.now()
        count_dict["datetime"] = date_time.strftime("%Y-%m-%d %H:%M:%S")
        count_dict["date"] = date_time.strftime("%Y-%m-%d")
        count_dict["source"] = index_name.split(".")[0]

        return count_dict

    @staticmethod
    def index_data_to_opensearch(df, index_name, qc_data_log, include_id=False):
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

        # Retrieve data, preprocess, and convert to dictionary

        dict_list = df.to_dict(orient="records")
        # Initialize counters and lists
        successful_records = 0
        failed_records = []

        # Prepare actions for bulk indexing
        actions = [
            {
                "_index": index_name,
                "_id": record["id"] if include_id else record["documentID"],
                "_op_type": "update",
                "doc": record,
                "doc_as_upsert": True,  # Upsert if document doesn't exist
            }
            for record in dict_list
        ]
        # Perform bulk indexing
        try:
            success, failed_items = bulk(client, actions=actions, raise_on_error=False)
            successful_records = success

            # `failed_items` is a list of failed operations, check and store them
            if failed_items:
                for failure in failed_items:
                    failed_records.append((failure, index_name.split(".")[0]))

        except Exception as e:
            # Raise the first encountered error instead of appending all records
            raise RuntimeError(f"Bulk indexing failed: {str(e)}")
            # success, _ = bulk(client, actions=actions)
            # successful_records = success
        # except Exception as e:
        #     # Log and store failed records
        #     for record in dict_list:
        #         failed_records.append((record, str(e), index_name.split(".")[0]))
        #         # logging.error(f"Failed to index document {record['_id']}: {e}")
        try:
            client.index(
                index=app_configs["ingress_analytics_log_index"], body=qc_data_log
            )
        except Exception as e:
            raise
        return successful_records, len(failed_records)
