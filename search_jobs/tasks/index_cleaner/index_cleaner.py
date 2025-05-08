from datetime import datetime, timedelta
from opensearchpy.helpers import scan, bulk
from opensearchpy import OpenSearch, helpers
from app.config import app_config
from app.config.env import environment
from app.sql_app.dbenums.core_enums import SourceEnum
from batch_jobs.enums.ingress_enums import JobType
from batch_jobs.internal.scheduler.task import Task
from batch_jobs.tasks.KZ.kz import KZLoader
from batch_jobs.tasks.doccebo.doccebo_course_delta import DoceboCourseDeltaLoader
from batch_jobs.tasks.kaas.kaas import KaasAPI
import pandas as pd
from batch_jobs.tasks.utils.analytics import DataQualityProcessor

app_configs = app_config.AppConfig.get_all_configs()
phase1_index = app_config.AppConfig.get_sectionwise_configs('index_values')


class OpenSearchManager(Task):

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

    def __init__(self):
        super().__init__("IndexCleaningTask")

    def run(self):
        super().run()
        self.index_cleaning_job()

    @staticmethod
    def fetch_all_documents(index_name):
        """Fetches all documents from the specified index."""
        query = {"query": {"match_all": {}}}
        results = scan(OpenSearchManager.client, query=query, index=index_name)
        return results

    @staticmethod
    def fetch_and_update_missing_documents(index_name, document_id_series):
        documents_to_update = []

        # Fetch all documents from the index
        results = OpenSearchManager.fetch_all_documents(index_name)
        # Extract the document IDs from the DataFrame for comparison
        df_document_ids = document_id_series.astype(str).tolist()

        # Iterate over the fetched results
        for res in results:
            # If the documentID is not found in the DataFrame, mark it as 'rejected'
            if res["_id"] not in df_document_ids:
                # Remove the 'query_embedding' field if it exists
                res["_source"].pop("query_embedding", None)
                res["_source"]["Doc_Status"] = "deleted"
                documents_to_update.append(res)

        # Prepare the documents for bulk update
        actions = [
            {
                "_op_type": "update",
                "_index": index_name,
                "_id": doc["_id"],
                "doc": doc["_source"],
            }
            for doc in documents_to_update
        ]

        # Perform the bulk update
        helpers.bulk(OpenSearchManager.client, actions)

        return f"{len(documents_to_update)} documents updated with 'deleted' in Doc_Status and 'query_embedding' removed in index '{index_name}'"

    @staticmethod
    def clean_dashboard_data(index_name, source, test_df):

        results = OpenSearchManager.fetch_all_documents(index_name)
        test = [res["_source"] for res in results]
        cd_df = pd.DataFrame(test)
        cd_df = cd_df[cd_df["Source"] == source]

        # Identify unmatched records
        df_document_ids = set(test_df["documentID"].astype(str).tolist())
        cd_df["documentID"] = cd_df["documentID"].astype(str)

        # Records in cd_df but not in test_df
        unmatched_records = cd_df[~cd_df["documentID"].isin(df_document_ids)]
        actions = [
            {
                "_op_type": "update",
                "_index": index_name,
                "_id": row['id'] if source == 'docebo' else row['documentID'],
                "doc": {"Doc_Status": "deleted"},
            }
            for _, row in unmatched_records.iterrows()
        ]

        # Execute the bulk update
        if actions:
            helpers.bulk(OpenSearchManager.client, actions)
        return f"{len(actions)} documents updated with 'deleted' in Doc_Status and 'query_embedding' removed in index '{index_name}'"

    def index_cleaning_job(self):

        kz_loader = KZLoader(run_type=JobType.HISTORICAL)
        kz_raw_data_df = kz_loader.make_api_request()
        kz_preprocessed_df = kz_loader.preprocess_data(kz_raw_data_df)

        kaas_loader = KaasAPI(run_type=JobType.HISTORICAL)
        kaas_raw_data_df = kaas_loader.make_api_request()
        kaas_preprocessed_df = kaas_loader.preprocess_data(kaas_raw_data_df)

        docebo_loader = DoceboCourseDeltaLoader(run_type=JobType.HISTORICAL)
        docebo_raw_data_df = docebo_loader.fetch_doccebo_course_data()
        docebo_df = docebo_loader.preprocessing(docebo_raw_data_df)
        docebo_preprocessed_df = docebo_loader.get_persona(docebo_df)

        job1 = OpenSearchManager.fetch_and_update_missing_documents(
             phase1_index["kz"], kz_preprocessed_df["documentID"]
        )
        job2 = OpenSearchManager.fetch_and_update_missing_documents(
             phase1_index["kaas"], kaas_preprocessed_df["documentID"]
        )
        job3 = OpenSearchManager.fetch_and_update_missing_documents(
             phase1_index["docebo"], docebo_preprocessed_df["id"]
        )
        kaas_test_df = DataQualityProcessor.process_dataframe(
            kaas_preprocessed_df, app_configs["kaas"], False, False
        )
        docebo_test_df = DataQualityProcessor.process_dataframe(
            docebo_preprocessed_df, app_configs["docebo"], True, False
        )
        kz_test_df = DataQualityProcessor.process_dataframe(
            kz_preprocessed_df, app_configs["kz"], False, True
        )
        job4 = OpenSearchManager.clean_dashboard_data(
            app_configs["ingress_analytics_visualization_index"],
            SourceEnum.Kaas.value,
            kaas_test_df,
        )
        job5 = OpenSearchManager.clean_dashboard_data(
            app_configs["ingress_analytics_visualization_index"],
            SourceEnum.Docebo.value,
            docebo_test_df,
        )
        job6 = OpenSearchManager.clean_dashboard_data(
            app_configs["ingress_analytics_visualization_index"],
            SourceEnum.KZ.value,
            kz_test_df,
        )
        print(job1, job2, job3, job4, job5, job6)
