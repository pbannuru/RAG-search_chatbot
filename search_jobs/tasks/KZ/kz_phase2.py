import datetime
import fitz  # PyMuPDF
import requests, re
import pandas as pd
from io import BytesIO
from opensearchpy import OpenSearch, exceptions, helpers
from opensearchpy.helpers import bulk
from pandas import DataFrame
from concurrent.futures import ThreadPoolExecutor, as_completed
from bs4 import BeautifulSoup
import logging
from app.config import app_config
import time
from app.services.job_saves_service import JobSaveService
from app.sql_app.database import DbDepends
from batch_jobs.enums.ingress_enums import JobType
from batch_jobs.internal.scheduler.task import Task
from batch_jobs.tasks.KZ.kz import KZLoader
from app.config.env import environment
from batch_jobs.tasks.utils.utils import *

app_configs = app_config.AppConfig.get_all_configs()
phase1_index = app_config.AppConfig.get_sectionwise_configs('index_values')
phase2_index = app_config.AppConfig.get_sectionwise_configs("upgraded_search_index_values")

def left_over_formats_df(df1):
    df1['format']=df1['format'].str.lower().str.strip()
    rdf=df1[df1['format'].apply(lambda x:x not in ('pdf','htm','html'))]
    rdf['metadata']=rdf.apply(lambda row:row.to_dict(),axis=1)
    rdf['text']=rdf['metadata'].apply(lambda x: x['ti_desc_prod'])
    rdf=rdf[['metadata','text']]
    rdf['metadata'] = rdf['metadata'].apply(
        lambda x: {**x, 'page_number': 1} if isinstance(x, dict) else {'page_number': 1}
    )
    return rdf

def get_phase1_data(source):
    with DbDepends() as db:
        job_state_kaas_ph2 = JobSaveService(db).get_job_state("KzTask_phase2")
        kz_ph2_last_successful_run = job_state_kaas_ph2.last_successful_run

    result = KZLoader(run_type=JobType.INCREMENTAL,from_date=kz_ph2_last_successful_run)
    # result = KZLoader(run_type=JobType.INCREMENTAL)
    df = result.make_api_request()
    df1 = result.preprocess_data(df)
    df1['format']=df1['format'].str.lower().str.strip()
    df_source=df1[df1['Domain']==source]
    return df_source

class full_text_pdf1:

    @staticmethod
    def split_page(row,url):
        try:
            # Download the file from the provided URL
            response = requests.get(url, stream=True)
            response.raise_for_status()  # Ensure the request was successful
    
            # Load the PDF content using BytesIO
            file_stream = BytesIO(response.content)
    
            try:
                # Attempt to load and process the PDF using PyMuPDF
                doc = fitz.open("pdf", file_stream)
                pages = [page.get_text("text") for page in doc]
                return pages
            except Exception as pdf_error:
                print(f"Failed to process the file as a PDF{row['documentID']}: {pdf_error}")
                return None
        except requests.exceptions.RequestException as e:
            print(f"Error processing URL: {url}. Error: {e}")
            return None

    @staticmethod
    def process_row(row, url_column):
        # Extract pages from the URL
        pages = full_text_pdf1.split_page(row, row[url_column])
        
        # If pages were successfully extracted, create records
        if pages is not None:
            metadata = row.drop(url_column).to_dict()  # Metadata dictionary
            
            records = []
            for page_num, page in enumerate(pages, start=1):
                meta_with_page_num = metadata.copy()
                meta_with_page_num['page_number'] = page_num  # Add page number
                
                records.append({
                    'metadata': meta_with_page_num,
                    'text': page
                })
            return records
        return []

    @staticmethod
    def preprocessing_pdf(df, url_column='preSignedUrl', max_workers=5):
        all_records = []
        
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            future_to_row = {executor.submit(full_text_pdf1.process_row, row, url_column): idx for idx, row in df.iterrows()}
            
            for future in as_completed(future_to_row):
                try:
                    records = future.result()
                    if records:
                        all_records.extend(records)
                except Exception as e:
                    print(f"Error processing row: {e}")
        
        return pd.DataFrame(all_records)

    @staticmethod
    def get_pdf_final(source):
        df_old = pd.DataFrame()
        df1 = get_phase1_data(source)
        df_doc = df1[df1['format']=='pdf']
        if df_doc.empty:
            return pd.DataFrame(columns=["metadata", "text"])
        batch_size = 500  
        
        for start in range(0, df_doc.shape[0], batch_size):
            end = start + batch_size
            df_batch = df_doc.iloc[start:end]  
            df_new = full_text_pdf1.preprocessing_pdf(df_batch, url_column='preSignedUrl', max_workers=10)
            df_old = pd.concat([df_old, df_new], ignore_index=True)
            df1 = get_phase1_data(source)
            df_doc = df1[df1['format']=='pdf']
        return df_old




class full_text_ingestion:

    @staticmethod
    def full_text_indexing(df: DataFrame):
        timeout_seconds = 1000
        index_name=phase2_index['kz']
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
        index_match_ids=get_ph2_existing_data(index_name,ids_list)
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
        return f"Number of successful records: {success_count}, failed records: {failure_count}"



class full_text_html:

    @staticmethod
    def extract_cleaned_content(soup):
        """Extract and clean content from HTML tags"""
        content = []
        for tag in soup.find_all(['p', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6']):
            text = ' '.join(tag.get_text().split())  # Clean and extract text
            if text:
                content.append(text)
        return content
    
    @staticmethod
    def fetch_and_process_document_content(url):
        """Fetch HTML content and clean the text"""
        try:
            page = requests.get(url,verify=False)  # Retrieve the page content
            html_content = page.content  # Store the HTML content
            
            # Parse the HTML content using BeautifulSoup
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # Extract and clean text from paragraphs, headlines, etc.
            content = full_text_html.extract_cleaned_content(soup)
            all_content = '\n'.join(content)  # Combine the extracted text
            
            # Return the cleaned content as text
            return all_content
        except Exception as e:
            logging.error(f"Error processing document from URL {url}: {e}")
            return None
    
    @staticmethod
    def process_row(row, url_column):
        """Process each row to extract content and combine metadata"""
        # Fetch and process the document content from the URL
        content = full_text_html.fetch_and_process_document_content(row[url_column])
        
        # If content was successfully fetched, create a record
        if content:
            # Create metadata dictionary from other columns, excluding the URL
            metadata = row.drop(url_column).to_dict()
    
            # Return the record as a dictionary
            return {
                'metadata': metadata,
                'text': content
            }
        return None
    
    @staticmethod
    def preprocessing(df, url_column='preSignedUrl', max_workers=5):
        """Process the DataFrame in parallel and create records with metadata and text"""
        # List to hold all records
        all_records = []
        
        # Use ThreadPoolExecutor for parallel processing
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            # Submit each row for processing in parallel
            future_to_row = {executor.submit(full_text_html.process_row, row, url_column): idx for idx, row in df.iterrows()}
            
            # Gather results as they complete
            for future in as_completed(future_to_row):
                try:
                    record = future.result()
                    if record:
                        all_records.append(record)
                except Exception as e:
                    logging.error(f"Error processing row: {e}")
        
        # Return a DataFrame with separate columns for metadata and text
        return pd.DataFrame(all_records)
        
    @staticmethod    
    def get_html_final(source):
        df1=get_phase1_data(source)
        if df1.empty:
            return pd.DataFrame(columns=["metadata", "text"])
        html_df=df1[df1['format'].apply(lambda x:x in ('htm','html'))]

        processed_html_df = full_text_html.preprocessing(html_df, max_workers=20)
        if processed_html_df.empty:
            return pd.DataFrame(columns=["metadata", "text"])
        
        processed_html_df['metadata'] = processed_html_df['metadata'].apply(
            lambda x: {**x, 'page_number': 1} if isinstance(x, dict) else {'page_number': 1}
        )
        return processed_html_df
    
class kzProcessorph2(Task):
    # this performs final operation
    def __init__(self):
        super().__init__("KzTask_phase2")

    def run(self):
        super().run()
        self.kzProcessorph2_job()

    @staticmethod    
    def limit_repeated_characters(text):
        """Replace any character repeated more than 5 times with 5 repetitions"""
        return re.sub(r'([\W_])(?:\s*\1){5,}', r'\1 ' * 5, text)
    
    @staticmethod
    def run_source(df1, domain):
        source_df=df1[df1['Domain']==domain]
        if source_df.empty:
            return f"no data for domain: {domain}"
        full_texthtml_df = full_text_html.get_html_final(domain)
        full_textpdf_df = full_text_pdf1.get_pdf_final(domain)
        finaldf = pd.concat([full_textpdf_df, full_texthtml_df], ignore_index=True)
        finaldf['text'] = finaldf['metadata'].apply(lambda x: x.get('ti_desc_prod', '')) +'. '+ finaldf['text']
        finaldf['text'] = finaldf['text'].apply(lambda x: kzProcessorph2.limit_repeated_characters(x))
        if finaldf.empty:
            return f"no data to index for domain{domain}"
        finaldf_result = full_text_ingestion.full_text_indexing(finaldf)
        return finaldf_result
    
    @staticmethod
    def kzProcessorph2_job():
        with DbDepends() as db:
            job_state_kaas_ph2 = JobSaveService(db).get_job_state("KzTask_phase2")
            kz_ph2_last_successful_run = job_state_kaas_ph2.last_successful_run

        result = KZLoader(run_type=JobType.INCREMENTAL,from_date=kz_ph2_last_successful_run)
        
        # Step 1: Fetch API Data
        df = result.make_api_request()
        if df.empty:
            print("API returned an empty DataFrame. Exiting process.")
            return "No data received from API."
        
        print(f"Initial DataFrame shape: {df.info()}")
        
        # Step 2: Preprocess Data
        df1 = result.preprocess_data(df)
        if df1.empty:
            print("Preprocessed DataFrame is empty. Exiting process.")
            return "No data after preprocessing."
        
        indigo_kz_result= kzProcessorph2.run_source(df1,'Indigo')
        pwp_kz_result= kzProcessorph2.run_source(df1,'PWP')
        scitex_kz_result= kzProcessorph2.run_source(df1,'scitex')
        threed_kz_result= kzProcessorph2.run_source(df1,'ThreeD')

        rdf = left_over_formats_df(df1)
        if rdf.empty:
            print("Leftover formats DataFrame is empty.")
            rdf_result = "No leftover formats."
        else:
            rdf_result = full_text_ingestion.full_text_indexing(rdf)

        return f"finaldf_result: {indigo_kz_result},{pwp_kz_result},{scitex_kz_result},{threed_kz_result}, rdf_result: {rdf_result}"

