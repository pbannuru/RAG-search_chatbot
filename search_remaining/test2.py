
import asyncio
import datetime

from IPython import embed
from app.config import app_config
from app.internal.utils.opensearch_utils import OpenSearchUtils
from app.services.core_search_service_upgraded import CoreSearchService
from app.services.opensearch_service import OpenSearchService
from app.sql_app.database import DbDepends
from app.sql_app.dbenums.core_enums import *
from batch_jobs.enums.ingress_enums import JobType
from batch_jobs.tasks.KZ.kz import KZLoader
from batch_jobs.tasks.doccebo.doccebo_course_delta import DoceboCourseDeltaLoader
from batch_jobs.tasks.doccebo.docebo_phase2 import doceboProcessorph2
from batch_jobs.tasks.index_cleaner.index_cleaner_ph2 import index_cleaner_ph2
from batch_jobs.tasks.kaas.kaas import KaasAPI
from batch_jobs.tasks.utils.analytics import DataQualityProcessor
from batch_jobs.tasks.utils.utils import get_ph2_existing_data
OpenSearchUtils.init()

app_configs = app_config.AppConfig.get_all_configs()

# async def main():
#     service = CoreSearchService()
#     result = await service.search(
#         query="12 million impressions for indigo 10k press",
#         domain=DomainEnum.Indigo,
#         device="",
#         persona=PersonaEnum.Engineer,
#         size=20,
#         source=[SourceEnum.All],
#         language=LanguageEnum.English,
#     )
#     print(result)
# final_result = asyncio.run(main())

# query="12 million impressions for indigo 10k press"
# domain=DomainEnum.Indigo
# device=""
# persona=PersonaEnum.Engineer
# size=20
# source=[SourceEnum.All]
# language=LanguageEnum.English

# response = OpenSearchService.get_search_response(
#     query, domain, device, persona, size, source, language
# )
kz_loader = KZLoader(run_type=JobType.HISTORICAL)
kz_raw_data_df = kz_loader.make_api_request()

kz_preprocessed_df = kz_loader.preprocess_data(kz_raw_data_df)

# kaas_loader = KaasAPI(run_type=JobType.HISTORICAL)
# kaas_raw_data_df = kaas_loader.make_api_request()
# kaas_preprocessed_df = kaas_loader.preprocess_data(kaas_raw_data_df)

# docebo_loader = DoceboCourseDeltaLoader(run_type=JobType.HISTORICAL)
# docebo_raw_data_df = docebo_loader.fetch_doccebo_course_data()
# docebo_df = docebo_loader.preprocessing(docebo_raw_data_df)
# docebo_preprocessed_df = docebo_loader.get_persona(docebo_df)
    

# # Only for testing purpose
# results = []
# #Created a tuple for each of the source
# for idx_name, df, label in [
#     ("knowledge-ph2-18", kz_preprocessed_df, 'kz'),
#     ("alias-docebo-phase2", docebo_preprocessed_df, 'docebo'),
#     ("alias-kaas-phase2",   kaas_preprocessed_df, 'kaas'),
# ]:
#     # resetting guard
#     index_cleaner_ph2.initialized = False

#     #initializig
#     index_cleaner_ph2.initialize(idx_name, df)
#     # print(len(index_cleaner_ph2.get_index_data_difference))
#     print('leftover_set',len(index_cleaner_ph2.leftover_set))
#     print('leftover_data',len(index_cleaner_ph2.leftover_data))
#     print('ids_to delete',len(index_cleaner_ph2.ids_to_delete))
#     if(label == "kz"):
#         qc_df = DataQualityProcessor.process_dataframe(
#             df, idx_name, False, True
#         )
#         print(qc_df.shape)
    
#     elif(label == "kaas"):
#         qc_df = DataQualityProcessor.process_dataframe(
#             df, idx_name, False, False
#         )
        
#     else:
#         qc_df = DataQualityProcessor.process_dataframe(
#             df, idx_name, True, False
#         )
        
#     qc_data_log = DataQualityProcessor.generate_qc_data_log(
#         qc_df, idx_name
#     )
    
#     DataQualityProcessor.index_data_to_opensearch(
#         qc_df,
#         app_configs["ingress_analytics_visualization_index"],
#         qc_data_log,
#     )
    
#     #Stopping the rest of processing if there is no data to be deleted
#     if not index_cleaner_ph2.ids_to_delete:
#         print(f"{label}: No records to delete or log")
#         results.append((label,0,0))
#         continue
        
#     # 2) delete from phase2 index
#     index_cleaner_ph2.perform_index_datadelete(idx_name)

#     # 3) preparing the logging data
#     deleted_df = index_cleaner_ph2.deleted_data(index_cleaner_ph2.leftover_data, label)

#     # 4) logging the deleted data
#     log_count = index_cleaner_ph2.log_deleted_records(deleted_df)
#     results.append((label, len(deleted_df),deleted_df))

# embed()


