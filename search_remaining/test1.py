from IPython import embed
from app.config import app_config
from app.services.job_saves_service import JobSaveService
from app.sql_app.database import DbDepends
from batch_jobs.enums.ingress_enums import JobType
from batch_jobs.tasks.KZ.kz import KZLoader
from batch_jobs.tasks.KZ.kz_phase2 import full_text_html, full_text_ingestion, full_text_pdf1, kzProcessorph2, left_over_formats_df
from batch_jobs.tasks.doccebo.doccebo_course_delta import DoceboCourseDeltaLoader
from batch_jobs.tasks.doccebo.docebo_phase2 import doceboProcessorph2
from batch_jobs.tasks.index_cleaner.index_cleaner_ph2 import index_cleaner_ph2
from batch_jobs.tasks.kaas.kaas import KaasAPI
from batch_jobs.tasks.kaas.kaas_phase2 import kaasProcessorph2
from batch_jobs.tasks.utils.analytics import DataQualityProcessor
from opensearchpy.helpers import scan
import pandas as pd

app_configs = app_config.AppConfig.get_all_configs()
phase1_index = app_config.AppConfig.get_sectionwise_configs('index_values')


# kaas_loader = KaasAPI(run_type=JobType.HISTORICAL)
# kaas_raw_data_df = kaas_loader.make_api_request()
# kaas_preprocessed_df = kaas_loader.preprocess_data(kaas_raw_data_df)
# print(kaas_preprocessed_df.shape)



# kaas = KaasAPI1(run_type=JobType.HISTORICAL)
# df=kaas.make_api_request()
# kaas_loader = KaasAPI(run_type=JobType.INCREMENTAL)

# # Fetch raw data from the API
# kaas_raw_data_df = kaas_loader.make_api_request()

# # Preprocess the fetched data
# df1 = kaas_loader.preprocess_data(kaas_raw_data_df)
# embed()
# print(df1.info())
# # indigo_result=kaasProcessorph2.index_source(df1,domain='Indigo')
# pwp_result=kaasProcessorph2.index_source(df1,domain='PWP')
# print(pwp_result)
# threed_result=kaasProcessorph2.index_source(df1,domain='ThreeD')

# sc_result=kaasProcessorph2.index_source(df1,domain='scitex')
# ind_result=kaasProcessorph2.index_source(df1,domain='Indigo')

# with DbDepends() as db:
#     job_state_kaas_ph2 = JobSaveService(db).get_job_state("KzTask_phase2")
#     kz_ph2_last_successful_run = job_state_kaas_ph2.last_successful_run

result = KZLoader(run_type=JobType.HISTORICAL)

# Step 1: Fetch API Data
df = result.make_api_request()
if df.empty:
    print("API returned an empty DataFrame. Exiting process.")
    print( "No data received from API.")

print(f"Initial DataFrame shape: {df.info()}")

# Step 2: Preprocess Data
df1 = result.preprocess_data(df)
if df1.empty:
    print("Preprocessed DataFrame is empty. Exiting process.")

# embed()
# indigo_kz_result= kzProcessorph2.run_source(df1,'Indigo')
# pwp_kz_result= kzProcessorph2.run_source(df1,'PWP')
# scitex_kz_result= kzProcessorph2.run_source(df1,'scitex')
# threed_kz_result= kzProcessorph2.run_source(df1,'ThreeD')

# rdf = left_over_formats_df(df1)
# if rdf.empty:
#     print("Leftover formats DataFrame is empty.")
#     rdf_result = "No leftover formats."
# else:
#     rdf_result = full_text_ingestion.full_text_indexing(rdf)
domain = 'Indigo'
source_df=df1[df1['Domain']==domain]

full_texthtml_df = full_text_html.get_html_final(domain)
full_textpdf_df = full_text_pdf1.get_pdf_final(domain)
finaldf = pd.concat([full_textpdf_df, full_texthtml_df], ignore_index=True)
finaldf['text'] = finaldf['metadata'].apply(lambda x: x.get('ti_desc_prod', '')) +'. '+ finaldf['text']
finaldf['text'] = finaldf['text'].apply(lambda x: kzProcessorph2.limit_repeated_characters(x))
embed()

from opensearchpy import OpenSearch, exceptions, helpers
from app.config.env import environment
import time

timeout_seconds = 1000
index_name='knowledge-ph2-21'
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
dict_list = finaldf.to_dict(orient="records")
success_count = 0  # Counter for successful operations
failure_count = 0  # Counter for failed operations

# Chunk the records into groups of 2
chunk_size = 1
chunks = [dict_list[i:i + chunk_size] for i in range(0, len(dict_list), chunk_size)]

# Loop through chunks of 2 records
for chunk in chunks:
    actions = []
    for record in chunk:
        action = {
            "_index": index_name,
            "_id": f"{record['metadata']['documentID']}_{record['metadata']['page_number']}",
            # "pipeline": "ingestion_pipeline_ph2",  # Optional ingestion pipeline
            "_op_type": "update",
            "doc": record,
            "doc_as_upsert": True,
        }
        actions.append(action)
    
    try:
        # Perform bulk indexing for 2 records at a time
        success, _ = helpers.bulk(client, actions)
        success_count += success  # Increment success counter by number of successes
    except exceptions.OpenSearchException as e:
        failure_count += len(chunk)  # Increment failure counter by chunk size
        print(f"Error indexing records: {e}")

    time.sleep(1)
print( f"Number of successful records: {success_count}, failed records: {failure_count}")