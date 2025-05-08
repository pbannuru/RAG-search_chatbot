# index cleaning mechanism
import datetime
from opensearchpy import OpenSearch
import pandas as pd
from app.config import app_config
from app.config.env import environment
from opensearchpy.helpers import scan
from opensearchpy import OpenSearch, helpers
from opensearchpy.helpers import bulk
from batch_jobs.enums.ingress_enums import JobType
from batch_jobs.internal.scheduler.task import Task
from batch_jobs.tasks.KZ.kz import KZLoader
from batch_jobs.tasks.doccebo.doccebo_course_delta import DoceboCourseDeltaLoader
from batch_jobs.tasks.kaas.kaas import KaasAPI
from batch_jobs.tasks.utils.analytics import DataQualityProcessor

app_configs = app_config.AppConfig.get_all_configs()
phase1_index = app_config.AppConfig.get_sectionwise_configs("index_values")


#Add task here in arguments
class index_cleaner_ph2(Task):
    
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
        super().__init__("IndexCleanerTask")

    def run(self):
        super().run()
        self.index_cleaner_ph2_job()

    # Class variables
    leftover_set = None
    leftover_data = None
    ids_to_delete = None
    initialized = False  # Guard to run only once
    
    #Change : added this df1 in argumnets
    @classmethod
    def initialize(cls, index_name,df1):
        if not cls.initialized:
            cls.leftover_set = cls.get_index_data_difference(index_name, df1)
            cls.leftover_data, cls.ids_to_delete = cls.get_todelete_records(index_name, cls.leftover_set)
            cls.initialized = True
            print("Initialization complete.")
        else:
            print("Already initialized. Skipping...")
            
    @staticmethod
    def get_index_data_difference(index_name, df1):
        query = {"query": {"match_all": {}}}
        results = scan(index_cleaner_ph2.client, query=query, index=index_name)
        documents_to_update = {res['_source']['metadata']['documentID'] for res in results}
        df1set = set(df1['documentID'].to_list())
        return documents_to_update - df1set
    
    @staticmethod
    def get_todelete_records(index_name, leftover_set):
        if not leftover_set:
            return pd.DataFrame(), []
        query = {
            "query": {
                "terms": {
                    "metadata.documentID.keyword": list(leftover_set)
                }
            },
            "_source": True
        }
        results = scan(index_cleaner_ph2.client, query=query, index=index_name, preserve_order=True)
        leftover_data = []
        ids_to_delete = []
        for res in results:
            leftover_data.append(res['_source'])
            ids_to_delete.append(res['_id'])
        leftover_df=pd.DataFrame(leftover_data)
        # leftover_df = leftover_df['metadata']
        return leftover_df, ids_to_delete
    
    @classmethod
    def perform_index_datadelete(cls, index_name):
        if cls.ids_to_delete:
            actions = [
                {
                    "_op_type": "delete",
                    "_index": index_name,
                    "_id": doc_id
                }
                for doc_id in cls.ids_to_delete
            ]
            try:
                success_count, errors = helpers.bulk(cls.client, actions)
                print(f"Deleted {success_count} documents")
                if errors:
                    print(f"Encountered {len(errors)} errors during deletion")
            except Exception as e:
                print(f"Bulk delete failed: {str(e)}")
        else:
            print("No documents to delete")

            
    #Made few changes like removing that left_df_set and adding those source, doc_status, deletedate on top        
    @staticmethod
    def deleted_data(leftover_data,source):
        if leftover_data.empty:
            return pd.DataFrame(columns=['documentID','persona','title','description','contentUpdateDate','Doc_Status','language','Domain'])
        left_df=leftover_data
        # left_df_set=set(left_df['metadata'].apply(lambda x: x.get('documentID')).to_list())
        left_df=pd.json_normalize(left_df['metadata'])
        left_df['documentID']=left_df['documentID'].astype('str')
        left_df=left_df.drop_duplicates(subset='documentID')
        left_df['Source']=source
        left_df['Doc_Status']='Deleted'
        left_df['DeletedDate'] = datetime.date.today()
        left_df=left_df[['documentID','persona','title','description','contentUpdateDate','Doc_Status','language','Domain']]
        return left_df
    
    #Created new function to log the deleted records i.e left_df returned by previous method, same as previous just added the empty check
    @staticmethod
    def log_deleted_records(left_df):
        if left_df.empty:
            print("No records deleted")
            return 0
        
        dict_list = left_df.to_dict(orient="records")
        index_name='delete_entry_index'
        
        # Prepare actions for bulk indexing with upsert
        actions = []
        for record in dict_list:
            action = {
                "_index": index_name,
                "_id": record["documentID"],
                "_op_type": "update",
                "doc": record,
                "doc_as_upsert": True,
            }
            actions.append(action)
        
        success, _ = bulk(index_cleaner_ph2.client, actions=actions)
        successful_records = success
    
    @staticmethod
    def index_cleaner_ph2_job():
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
         
      
        # Only for testing purpose
        results = []
        #Created a tuple for each of the source
        for idx_name, df, label in [
            ("knowledge-ph2-18", kz_preprocessed_df, 'kz'),
            ("alias-docebo-phase2", docebo_preprocessed_df, 'docebo'),
            ("alias-kaas-phase2",   kaas_preprocessed_df, 'kaas'),
        ]:
            # resetting guard
            index_cleaner_ph2.initialized = False

            #initializig
            index_cleaner_ph2.initialize(idx_name, df)
            
            if(label == "kz"):
                qc_df = DataQualityProcessor.process_dataframe(
                    df, idx_name, False, True
                )
            
            elif(label == "kaas"):
                 qc_df = DataQualityProcessor.process_dataframe(
                    df, idx_name, False, False
                )
                
            else:
                 qc_df = DataQualityProcessor.process_dataframe(
                    df, idx_name, True, False
                )
                
            qc_data_log = DataQualityProcessor.generate_qc_data_log(
                qc_df, idx_name
            )
            
            DataQualityProcessor.index_data_to_opensearch(
                qc_df,
                app_configs["ingress_analytics_visualization_index"],
                qc_data_log,
            )
            
            #Stopping the rest of processing if there is no data to be deleted
            if not index_cleaner_ph2.ids_to_delete:
                print(f"{label}: No records to delete or log")
                results.append((label,0,0))
                continue
                
            # 2) delete from phase2 index
            index_cleaner_ph2.perform_index_datadelete(idx_name)

            # 3) preparing the logging data
            deleted_df = index_cleaner_ph2.deleted_data(index_cleaner_ph2.leftover_data, label)

            # 4) logging the deleted data
            log_count = index_cleaner_ph2.log_deleted_records(deleted_df)
            print(f"{label}: Completed delete & log for {len(deleted_df)} records")
            #These results are for testing purpose 
            results.append((label, len(deleted_df),deleted_df))
        return results
