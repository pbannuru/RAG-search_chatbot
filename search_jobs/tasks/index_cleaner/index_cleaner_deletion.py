from datetime import datetime, timedelta
from opensearchpy.helpers import scan, bulk
from opensearchpy import OpenSearch, helpers
from app.config import app_config
from app.config.env import environment
from batch_jobs.internal.scheduler.task import Task

app_configs = app_config.AppConfig.get_all_configs()
phase1_index = app_config.AppConfig.get_sectionwise_configs('index_values')

class index_data_deletion(Task):

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
        super().__init__("IndexCleaningDeletionTask")

    def run(self):
        super().run()
        last_successful_run = self.last_successful_run
        self.last_successful_run.strftime("%d/%m/%Y %H:%M:%S")
        if last_successful_run and datetime.utcnow() - last_successful_run >= timedelta(days=15):
         
            self.index_cleaning_deletion_job()

    @staticmethod
    def fetch_all_documents(index_name):
        """Fetches all documents from the specified index."""
        query = {"query": {"match_all": {}}}
        results = scan(index_data_deletion.client, query=query, index=index_name)
        return results

    @staticmethod
    def process_and_delete_records(index_name):
        """Fetches, filters, and deletes records with Doc_Status 'deleted'."""
        results = index_data_deletion.fetch_all_documents(index_name)
        actions = []

        for record in results:
            if record["_source"].get("Doc_Status") == "deleted":
                actions.append(
                    {"_op_type": "delete", "_index": index_name, "_id": record["_id"]}
                )

        if actions:
            bulk(index_data_deletion.client, actions)
            return f"{len(actions)} documents deleted in '{index_name}'"
        
    def index_cleaning_deletion_job(self):
        job1=index_data_deletion.process_and_delete_records( phase1_index["kaas"])
        job2=index_data_deletion.process_and_delete_records( phase1_index["docebo"])
        job3=index_data_deletion.process_and_delete_records( phase1_index["kz"])
        job4=index_data_deletion.process_and_delete_records( phase1_index["ingress_analytics_visualization_index"])
        print(job1,job2,job3,job4)