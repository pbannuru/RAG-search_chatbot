from IPython import embed
from app.config import app_config
from batch_jobs.enums.ingress_enums import JobType
from batch_jobs.tasks.KZ.kz import KZLoader
from batch_jobs.tasks.KZ.kz_phase2 import kzProcessorph2
from batch_jobs.tasks.doccebo.doccebo_course_delta import DoceboCourseDeltaLoader
from batch_jobs.tasks.doccebo.docebo_phase2 import doceboProcessorph2
from batch_jobs.tasks.index_cleaner.index_cleaner_ph2 import index_cleaner_ph2
from batch_jobs.tasks.kaas.kaas import KaasAPI
from batch_jobs.tasks.kaas.kaas_phase2 import kaasProcessorph2
from batch_jobs.tasks.utils.analytics import DataQualityProcessor
from opensearchpy.helpers import scan


app_configs = app_config.AppConfig.get_all_configs()
phase1_index = app_config.AppConfig.get_sectionwise_configs('index_values')

kz_loader = KZLoader(run_type=JobType.HISTORICAL)
kz_raw_data_df = kz_loader.make_api_request()
kz_preprocessed_df = kz_loader.preprocess_data(kz_raw_data_df)

# kaas_loader = KaasAPI(run_type=JobType.HISTORICAL)
# kaas_raw_data_df = kaas_loader.make_api_request()
# kaas_preprocessed_df = kaas_loader.preprocess_data(kaas_raw_data_df)
# print(kaas_preprocessed_df.shape)

query = {
    "query": {
        "match_all": {}
    }
}
index_name='knowledge-ph2-18'
results = scan(index_cleaner_ph2.client, query=query, index=index_name)
documents_to_update = set()
for res in results:
    documents_to_update.add(res['_source']['metadata']['documentID'])

df1set=set(kz_preprocessed_df['documentID'].to_list())
leftover_set=documents_to_update-df1set

query = {
    "query": {
        "terms": {
            "metadata.documentID.keyword": list(leftover_set)
        }
    },
    "_source": False  # We only need the _id, not the full document
}
# 2. Scan to get all matching document _ids
results = scan(index_cleaner_ph2.client,query=query,index=index_name,preserve_order=True)

# 3. Collect the OpenSearch _ids to delete
ids_to_delete = [hit['_id'] for hit in results]

# docebo_loader = DoceboCourseDeltaLoader(run_type=JobType.HISTORICAL)
# docebo_raw_data_df = docebo_loader.fetch_doccebo_course_data()
# docebo_df = docebo_loader.preprocessing(docebo_raw_data_df)
# docebo_preprocessed_df = docebo_loader.get_persona(docebo_df)
# query = {"query": {"match_all": {}}}
# results = scan(index_cleaner_ph2.client, query=query, index='alias-kaas-phase2')
# documents_to_update = set()
# for res in results:
#     documents_to_update.add(res["_source"]["metadata"]["documentID"])

# df1set = set(kaas_preprocessed_df["documentID"].to_list())
# leftover_set = documents_to_update - df1set

# kz_leftover_set= index_cleaner_ph2.get_index_data_difference('knowledge-ph2-18',kz_preprocessed_df)
# kz_index_cleaner_ph2= index_cleaner_ph2.delete_records('knowledge-ph2-18',kz_leftover_set)
# docebo_leftover_set = index_cleaner_ph2.get_index_data_difference('alias-docebo-phase2',docebo_preprocessed_df)
# docebo_index_cleaner_ph2 = index_cleaner_ph2.delete_records('alias-docebo-phase2',docebo_leftover_set)
# kaas_leftover_set = index_cleaner_ph2.get_index_data_difference('alias-kaas-phase2',kaas_preprocessed_df)
# kaas_index_cleaner_ph2=index_cleaner_ph2.delete_records('alias-docebo-phase2',kaas_leftover_set)
# print(kz_leftover_set,docebo_leftover_set,kaas_leftover_set)

embed()
