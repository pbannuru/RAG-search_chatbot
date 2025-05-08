import pandas as pd
import re, logging, time, requests
from typing import Tuple
from io import BytesIO
from PyPDF2 import PdfReader
from app.services.job_saves_service import JobSaveService
from app.sql_app.database import DbDepends
from batch_jobs.internal.scheduler.task import Task
from batch_jobs.tasks.utils.utils import *
from concurrent.futures import ThreadPoolExecutor, as_completed
from bs4 import BeautifulSoup
from opensearchpy import OpenSearch, exceptions, helpers
from pandas import DataFrame
from app.config import app_config
from app.config.env import environment

from batch_jobs.enums.ingress_enums import JobType
from batch_jobs.tasks.kaas.kaas import KaasAPI

app_configs = app_config.AppConfig.get_all_configs()
phase1_index = app_config.AppConfig.get_sectionwise_configs("index_values")
phase2_index = app_config.AppConfig.get_sectionwise_configs("upgraded_search_index_values")


class KaasProcessing_scitex:

    @staticmethod
    def get_bulk_render_url_updated(documentIDs):
        """Fetch render links for a list of document IDs in bulk."""
        bulk_render_url = app_configs['bulk_render_url'] #"https://css.api.hp.com/knowledge/v2/getRenderLinks"
        access_token = kaas_access_token()  # Ensure this function exists

        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {access_token}",
        }

        data = {
            "languageCode": "en",
            "requests": [{"languageCode": "en", "ids": documentIDs}],
        }

        response = requests.post(bulk_render_url, headers=headers, json=data)
        response.raise_for_status()  # Raises error for bad status codes
        response_json = response.json()

        # Dictionary to store documentID -> renderLink mapping
        renderlinks = {}
        if isinstance(response_json, list) and response_json:
            for item in response_json:
                if "renderLinks" in item:
                    for doc in item["renderLinks"]:
                        if "id" in doc and "renderLink" in doc:
                            renderlinks[doc["id"]] = doc["renderLink"]

        logging.info(
            f"Fetched {len(renderlinks)} URLs for {len(documentIDs)} document IDs."
        )
        return renderlinks

    @staticmethod
    def fetch_scitex_urls(df1, batch_size=500):
        """Fetch and categorize URLs for scitex domain documents."""
        results = []
        scitex_ids = df1[df1["Domain"] == "scitex"]["documentID"].to_list()

        for i in range(0, len(scitex_ids), batch_size):
            batch = scitex_ids[i : i + batch_size]
            urls = KaasProcessing_scitex.get_bulk_render_url_updated(
                batch
            )  # Returns {doc_id: url} dictionary
            results.extend(urls.items())

        scitexdf = pd.DataFrame(results, columns=["doc_id", "url"])
        return scitexdf

    @staticmethod
    def get_scitex_fdf(df1):
        scitexdf = KaasProcessing_scitex.fetch_scitex_urls(df1)
        testpdf = scitexdf.loc[
            (scitexdf["url"].str.contains("pdf"))
            & (~scitexdf["doc_id"].apply(lambda x: x.startswith("pdf")))
        ]
        scitex_pdf_df = df1[
            df1["documentID"].apply(lambda x: x in testpdf["doc_id"].to_list())
        ]
        testhtml = scitexdf[~scitexdf["url"].str.contains("pdf")]
        scitex_html_df = df1[
            df1["documentID"].apply(lambda x: x in testhtml["doc_id"].to_list())
        ]
        return scitex_pdf_df, scitex_html_df


def get_bulk_renderlink(documentIDs):
    """Fetches bulk render links for a list of document IDs."""
    bulk_render_url = app_configs['bulk_render_url'] #"https://css.api.hp.com/knowledge/v2/getRenderLinks"
    access_token = kaas_access_token()  # Assuming this function exists

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {access_token}",
    }

    data = {
        "languageCode": "en",
        "requests": [{"languageCode": "en", "ids": documentIDs}],
    }

    response = requests.post(bulk_render_url, headers=headers, json=data)
    response.raise_for_status()

    response_data = response.json()
    render_links = {
        i["id"]: i["renderLink"]
        for i in response_data[0]["renderLinks"]
        if "renderLink" in i
    }
    return render_links


class process_html:

    # Function to fetch and process content from each document in the batch
    @staticmethod
    def fetch_and_process_document_content(url, row):
        try:
            page = requests.get(url, verify=False)  # Retrieve the page content
            html_content = page.content  # Directly store the HTML content in memory

            # Parse the HTML content using BeautifulSoup
            soup = BeautifulSoup(html_content, "html.parser")

            # Extract and clean text from paragraphs, headlines, etc.
            content = process_html.extract_cleaned_content(soup)
            all_content = " \n".join(content)

            # Debugging: print out the document ID, URL, and the first part of the content
            logging.info(
                f'Processed document ID: {row["documentID"]} from URL: {url} \nContent: {all_content[:100]}'
            )

            # Return the document metadata and content
            return {"metadata": row.to_dict(), "text": all_content}
        except Exception as e:
            logging.error(f"Error processing document from URL {url}: {e}")
            return {"metadata": row.to_dict(), "text": None}

    # Function to process a batch of documents
    @staticmethod
    def process_batch(batch_rows):
        # Check if batch_rows is a DataFrame, and if so, iterate using .iterrows()
        if isinstance(batch_rows, pd.DataFrame):
            batch_rows = [
                row for _, row in batch_rows.iterrows()
            ]  # Convert rows to list of Series

        # Now batch_rows is a list of rows (Series or dict-like), safe to extract 'documentID'
        document_ids = [row["documentID"] for row in batch_rows]

        # Fetch URLs for the batch of document IDs as a dictionary {documentID: renderLink}
        url_mapping = get_bulk_renderlink(document_ids)

        # Use a thread pool to fetch and process each document's content in parallel
        results = []
        with ThreadPoolExecutor(max_workers=min(10, len(batch_rows))) as executor:
            futures = {
                executor.submit(
                    process_html.fetch_and_process_document_content,
                    url_mapping[row["documentID"]],
                    row,
                ): row["documentID"]
                for row in batch_rows
                if row["documentID"] in url_mapping
            }

            for future in as_completed(futures):
                result = future.result()
                if result:
                    results.append(result)

        return results

    # Function to split DataFrame into batches and process them in parallel
    @staticmethod
    def process_documents_in_parallel(df, batch_size=500, max_workers=10):
        data = []

        # Split the DataFrame into batches of `batch_size`
        batches = [df[i : i + batch_size] for i in range(0, len(df), batch_size)]

        # Process batches in parallel using ThreadPoolExecutor
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = [
                executor.submit(process_html.process_batch, batch) for batch in batches
            ]

            for future in as_completed(futures):
                batch_results = future.result()
                data.extend(batch_results)
        ish_df=pd.DataFrame(data)
        ish_df['metadata'] = ish_df['metadata'].apply(lambda x: {**x, 'page_number': 1})
        return ish_df

    @staticmethod
    def extract_cleaned_content(soup):
        content = []
        for tag in soup.find_all(["p", "h1", "h2", "h3", "h4", "h5", "h6"]):
            text = " ".join(
                tag.get_text().split()
            )  # Clean and extract text in one step
            if text:
                content.append(text)
        return content


class KaasPdfProcessing:

    @staticmethod
    def split_Page1(url):
        """Downloads and extracts text from a PDF URL."""
        try:
            response = requests.get(url, verify=False)
            if response.status_code == 200:
                file_stream = BytesIO(response.content)
                try:
                    reader = PdfReader(file_stream)
                    pages = [page.extract_text() for page in reader.pages]
                    return pages
                except Exception as pdf_error:
                    print(f"Failed to process the file as a PDF: {pdf_error}")
                    return None
            else:
                print(f"Failed to fetch URL: {url}")
                return None
        except Exception as e:
            print(f"Error processing URL: {url}. Error: {e}")
            return None

    @staticmethod
    def process_batch(batch, df, doc_id_column="documentID"):
        """Processes a batch of document IDs to extract page-level metadata."""
        records = []

        # Get render links for the document IDs in this batch
        document_ids = batch.tolist()
        url_mapping = get_bulk_renderlink(document_ids)

        for doc_id in document_ids:
            url = url_mapping.get(doc_id)

            if url:
                pages = KaasPdfProcessing.split_Page1(url)

                if pages is not None:
                    row = df[df[doc_id_column] == doc_id].iloc[0]
                    metadata = row.to_dict()

                    for page_num, page in enumerate(pages, start=1):
                        meta_with_page_num = metadata.copy()
                        meta_with_page_num["page_number"] = page_num

                        records.append({"metadata": meta_with_page_num, "text": page})
        return records

    @staticmethod
    def preprocessing_parallel(
        df, doc_id_column="documentID", batch_size=500, max_workers=4
    ):
        """Executes parallel processing of PDFs using ThreadPoolExecutor."""
        document_id_batches = [
            df[doc_id_column].iloc[i : i + batch_size]
            for i in range(0, len(df), batch_size)
        ]
        records = []

        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = {
                executor.submit(
                    KaasPdfProcessing.process_batch, batch, df, doc_id_column
                ): batch
                for batch in document_id_batches
            }

            for future in as_completed(futures):
                try:
                    result = future.result()
                    if result:
                        records.extend(result)
                except Exception as e:
                    print(f"Error processing batch: {e}")

        return pd.DataFrame(records)


class FullTextIngestion:
    @staticmethod
    def full_text_indexing(df: DataFrame):
        # Configuration for OpenSearch connection
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
        index_name = phase2_index['kaas']
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
        # Convert DataFrame to list of dictionaries
        dict_list = df.to_dict(orient="records")

        # Initialize counters for success and failure
        success_count = 0
        failure_count = 0

        # Chunk the records into groups of 1
        chunk_size = 1
        chunks = [
            dict_list[i : i + chunk_size] for i in range(0, len(dict_list), chunk_size)
        ]

        # Loop through chunks of records
        for chunk in chunks:
            actions = []
            for record in chunk:

                action = {
                    "_index": index_name,
                    "_id": f"{record['metadata']['documentID']}_{record['metadata']['page_number']}",
                    "pipeline": "openai_ingestion_vector_pipeline",
                    "_op_type": "update",
                    "doc": record,
                    "doc_as_upsert": True,
                }
                actions.append(action)

            try:
                # Perform bulk indexing
                success, _ = helpers.bulk(client, actions)
                success_count += (
                    success  # Increment success counter by number of successes
                )
            except exceptions.OpenSearchException as e:
                failure_count += len(chunk)  # Increment failure counter by chunk size
                print(f"Error indexing records: {e}")
            time.sleep(1)
        # Return the result of the indexing operation
        return f"Number of successful records: {success_count}, failed records: {failure_count}"

class kaasProcessorph2(Task):

    def __init__(self):
        super().__init__("KaasTask_phase2")

    def run(self):
        super().run()
        self.kaasProcessorph2_job()

    @staticmethod
    def limit_repeated_characters(text: str) -> str:
        """
        Replace any character repeated more than 5 times with 5 repetitions

        Args:
            text: Input text to process

        Returns:
            Processed text with limited character repetitions
        """
        return re.sub(r"([\W_])(?:\s*\1){5,}", r"\1 " * 5, text)


    @staticmethod
    def get_pdf_processed(pdf_df: pd.DataFrame):
        if pdf_df.empty:
            return pd.DataFrame(columns=["metadata", "text"])
        pdf_df = KaasPdfProcessing.preprocessing_parallel(
            pdf_df, doc_id_column="documentID", batch_size=500, max_workers=8
        )

        pdf_df["text"] = (
            pdf_df["metadata"].apply(lambda x: x.get("ti_desc_prod", ""))
            + ". "
            + pdf_df["text"]
        )
        pdf_df["text"] = pdf_df["text"].apply(
            lambda x: kaasProcessorph2.limit_repeated_characters(x)
        )

        return pdf_df

    @staticmethod
    def get_html_processed(html_df: pd.DataFrame):
        if html_df.empty:
            return pd.DataFrame(columns=["metadata", "text"])
        html_df = process_html.process_documents_in_parallel(
            html_df, batch_size=500, max_workers=20
        )

        html_df["text"] = (
            html_df["metadata"].apply(lambda x: x.get("ti_desc_prod", ""))
            + ". "
            + html_df["text"]
        )

        return html_df
        
    @staticmethod
    def get_pdf_html_details(df,batch_size=500):
        results = []
        ids = df["documentID"].to_list()
        
        for i in range(0, len(ids), batch_size):
            batch = ids[i : i + batch_size]
            urls = KaasProcessing_scitex.get_bulk_render_url_updated(
                batch
            )  # Returns {doc_id: url} dictionary
            results.extend(urls.items())
        
        df = pd.DataFrame(results, columns=["doc_id", "url"])
        return df
    
    @staticmethod   
    def index_source(df1,domain):
        source_df= df1[df1['Domain']==domain]
        if source_df.empty:
            return f"no data for domain {domain}"
        
        pdf_result = None
        html_result = None

        # if 'scitex' in domain.lower():
        sdf = kaasProcessorph2.get_pdf_html_details(source_df)
        sdf_pdf_df = sdf.loc[sdf["url"].str.contains("pdf")]
        sdf_html_df = sdf.loc[~sdf["url"].str.contains("pdf")]   
        pdf_df = df1[
            df1["documentID"].apply(lambda x: x in sdf_pdf_df["doc_id"].to_list())
        ]
        html_df = df1[
            df1["documentID"].apply(lambda x: x in sdf_html_df["doc_id"].to_list())
        ]
        # else:
        #     pdf_df = source_df[source_df["documentID"].apply(lambda x: x.startswith("pdf"))]

        #     html_df = source_df[source_df["documentID"].apply(lambda x: x.startswith("ish"))]


        processed_pdf = kaasProcessorph2.get_pdf_processed(pdf_df)
        if not processed_pdf.empty:
            pdf_result = FullTextIngestion.full_text_indexing(processed_pdf)
        processed_html = kaasProcessorph2.get_html_processed(html_df)
        # final_df = pd.concat([processed_pdf, processed_html], ignore_index=True)
        if not processed_html.empty:
            html_result = FullTextIngestion.full_text_indexing(processed_html)
        return (pdf_result,html_result)
        
    @staticmethod
    def kaasProcessorph2_job():
        with DbDepends() as db:
            job_state_kaas_ph2 = JobSaveService(db).get_job_state("KaasTask_phase2")
            kaas_ph2_last_successful_run = job_state_kaas_ph2.last_successful_run

        kaas_loader = KaasAPI(run_type=JobType.INCREMENTAL,from_date=kaas_ph2_last_successful_run)

        # Fetch raw data from the API
        kaas_raw_data_df = kaas_loader.make_api_request()
        if kaas_raw_data_df.empty:
            return f"no data retrieved from kaas"
        # Preprocess the fetched data
        df1 = kaas_loader.preprocess_data(kaas_raw_data_df)
        if df1.empty:
            return f"no data after preprocessing kaas"
        
        indigo_result=kaasProcessorph2.index_source(df1,domain='Indigo')
        pwp_result=kaasProcessorph2.index_source(df1,domain='PWP')
        scitex_result=kaasProcessorph2.index_source(df1,domain='scitex')
        threed_result=kaasProcessorph2.index_source(df1,domain='ThreeD')

        return f"{indigo_result}{pwp_result}{scitex_result}{threed_result}"
    