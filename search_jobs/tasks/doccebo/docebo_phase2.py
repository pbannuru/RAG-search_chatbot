import ast
import re
from app.config.env import environment
from app.services.job_saves_service import JobSaveService
from app.sql_app.database import DbDepends
from app.sql_app.dbenums.core_enums import DomainEnum
from batch_jobs.enums.ingress_enums import IngestionSourceEnum, JobType
from batch_jobs.internal.scheduler.task import Task
from batch_jobs.tasks.doccebo.doccebo_course_delta import DoceboCourseDeltaLoader
from batch_jobs.tasks.utils.analytics import DataQualityProcessor
from batch_jobs.tasks.utils.utils import *
import logging
from app.config import app_config
import requests
import pandas as pd
import datetime
import concurrent.futures
from concurrent.futures import ThreadPoolExecutor, as_completed
from opensearchpy import OpenSearch, exceptions, helpers
from opensearchpy.helpers import bulk
from pandas import DataFrame
from itertools import islice

class doceboProcessorph2(Task):
    def __init__(self):
        super().__init__("DoceboTask_phase2")

    def run(self):
        super().run()
        self.doceboProcessorph2_job()

    @staticmethod
    def full_text_data(df):
        df['metadata']=df.apply(lambda row:row.to_dict(),axis=1)
        df['text']=df['metadata'].apply(lambda x: x['ti_desc_prod'])
        df=df[['metadata','text']]
        return df
        
    @staticmethod
    def full_text_indexing(df):
        
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
        
        ids_list=df['metadata'].apply(lambda x: x.get('documentID')).to_list()
        index_match_ids=get_ph2_existing_data('alias-docebo-phase2',ids_list)
        updated_count=len(index_match_ids)
        new_count=len(ids_list)-len(index_match_ids)
        try:
            data_to_index = {
                "new_records": new_count,
                "updated_records": updated_count,
                "timestamp": datetime.datetime.now(),
                "index_loaded": index_name,
            }
            client.index(index="data_log_incremental", body=data_to_index)
            print("Successfully indexed data to data_log_incremental index.")
        except Exception as e:
            print(f"Failed to index data to data_log_incremental index: {e}")

        dict_list = df.to_dict(orient="records")
        batch_size = 5  # Adjust as per your requirements
        
        # Function to yield batches
        def chunked_iterable(iterable, size):
            iterator = iter(iterable)
            for first in iterator:  # take the first element
                yield [first] + list(islice(iterator, size - 1))  # build the batch
        
        # Prepare actions for bulk indexing with upsert
        index_name = 'alias-docebo-phase2'
        actions = []
        for record in dict_list:
            action = {
                "_index": index_name,
                "_id": record['metadata']['id'],
                # "pipeline": "ingestion_pipeline_ph2_1",
                "_op_type": "update",
                "doc": record,
                "doc_as_upsert": True,
            }
            actions.append(action)
        
        # Initialize counters
        successful_records = 0
        total_records = 0
        
        # Perform bulk indexing in batches
        for batch in chunked_iterable(actions, batch_size):
            success, _ = bulk(client, actions=batch)
            successful_records += success
            total_records += len(batch)
            print(f"Batch processed: {len(batch)}, Total successful: {successful_records}")
        
        print(f"Total successful records: {successful_records},Total failed records: {total_records-successful_records}")

    @staticmethod
    def doceboProcessorph2_job():
        with DbDepends() as db:
            job_state_kaas_ph2 = JobSaveService(db).get_job_state("DoceboTask_phase2")
            docebo_ph2_last_successful_run = job_state_kaas_ph2.last_successful_run
            
        docebo_loader = DoceboCourseDeltaLoader(run_type=JobType.INCREMENTAL,from_date=docebo_ph2_last_successful_run)
        docebo_raw_data_df = docebo_loader.fetch_doccebo_course_data()
        if not docebo_raw_data_df:
            return f"no data for docebo"
        docebo_df = docebo_loader.preprocessing(docebo_raw_data_df)
        if docebo_df.empty:
            return f"docebo df is empty"
        docebo_preprocessed_df = docebo_loader.get_persona(docebo_df)
        fdf = doceboProcessorph2.full_text_data(docebo_preprocessed_df)
        result=doceboProcessorph2.full_text_indexing(fdf)
        return result 


