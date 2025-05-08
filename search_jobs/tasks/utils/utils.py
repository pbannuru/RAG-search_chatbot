import re
from app.config import app_config
import requests
from app.config.env import environment
from fastapi_cache.decorator import cache
import datetime
import hashlib
import hmac
import requests
import pandas as pd
from opensearchpy import OpenSearch
from opensearchpy.helpers import scan
from opensearchpy.helpers import bulk
from app.sql_app.dbenums.core_enums import LanguageEnum

app_configs = app_config.AppConfig.get_all_configs()


@cache(expire=3600)
async def get_kaas_access_token():
    """
    Fetches an access token from the API using the provided configuration.
    Returns:
        str: The access token on success, throws on failure HTTPError 401 Unauthorized.
    """
    auth_url = app_configs["kaas_auth_url"]
    auth_params = {
        "grant_type": "client_credentials",
        "client_id": app_configs["kaas_auth_client_id"],
        "client_secret": environment.AUTH_KAAS_CLIENT_SECRET,
    }
    print("auth_params:", auth_params)
    response = requests.post(auth_url, data=auth_params)
    response.raise_for_status()
    auth_data = response.json()
    access_token = auth_data.get("access_token")
    return access_token


def kaas_access_token():
    auth_url = app_configs["kaas_auth_url"]
    auth_params = {
        "grant_type": "client_credentials",
        "client_id": app_configs["kaas_auth_client_id"],
        "client_secret": environment.AUTH_KAAS_CLIENT_SECRET,
    }

    response = requests.post(auth_url, data=auth_params)
    response.raise_for_status()
    auth_data = response.json()
    access_token = auth_data.get("access_token")
    return access_token


def get_doccebo_access_token():
    """
    Fetches an access token from the API using the provided configuration.
    Returns:
        str: The access token on success, throws on failure HTTPError 401 Unauthorized.
    """
    auth_url = app_configs["doccebo_auth_url"]
    user_credentials = {
        "username": app_configs["doccebo_auth_username"],
        "password": environment.AUTH_DOCCEBO_PASSWORD,
    }

    response = requests.post(auth_url, data=user_credentials)
    response.raise_for_status()
    access_token = response.json()["data"]["access_token"]

    return access_token


def create_params_kaas():
    """
    Generates product and disclosure level combinations for API requests based on configuration.
    Yields:
        tuple: A tuple containing (product ID, disclosure level).
    """
    path = app_configs["kaas_products"]
    df = pd.read_csv(path)
    # Extract product IDs from the DataFrame
    product_ids = df["product_id"].astype(str).tolist()  # Convert IDs to strings

    # Disclosure levels (replace with actual levels or a method to get them)
    disclosure_levels = [
        "47406819852170807613486806879990",
        "696531864679532034919979251200881",
        "887243771386204747508092376253257",
        "287477763180518087286275037723076",
        "218620138892645155286800249901443",
        "600096605536507071488362545356335",
    ]

    batch_size = 1  # Number of product IDs in a batch

    # Generate batches and yield combinations
    for i in range(0, len(product_ids), batch_size):
        batch_product_ids = product_ids[i : i + batch_size]
        combined_product_ids = ",".join(batch_product_ids)
        for dl in disclosure_levels:
            yield combined_product_ids, dl


def fetch_existing_documents(client, index_name, document_ids):
    try:
        response = client.mget(index=index_name, body={"ids": document_ids})
        return {doc["_id"]: doc["found"] for doc in response["docs"]}
    except Exception as e:
        return {}

def get_ph2_existing_data(index_name,ids_list):
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
    query = {
        "query": {
            "terms": {
                "metadata.documentID.keyword": ids_list
            }
        },
        "_source": True
    }
    
    results = scan(client, query=query, index=index_name, preserve_order=True)
    existing_data = set()
    for res in results:
        existing_data.add(res['_source']['metadata']['documentID'])
    return existing_data

def kz_create_headers():
    key = app_configs["kz_hmac_key"]
    secret = environment.AUTH_KZ_CLIENT_SECRET
    method = "GET"
    path = "/assetmanagement/list/offline"
    timestamp = datetime.datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")
    string_to_sign: str = method + " " + path + timestamp
    local_secret: bytes = secret.encode("utf-8")
    string_to_sign: bytes = string_to_sign.encode("utf-8")
    signature = hmac.new(local_secret, string_to_sign, hashlib.sha256).hexdigest()
    auth: str = key + ":" + signature
    return {
        "content-type": "application/json",
        "x-hp-hmac-authentication": auth,
        "x-hp-hmac-date": timestamp,
        "x-hp-hmac-algorithm": "SHA256",
    }


def kz_get_pwp_device_lookup():

    kz_pwp_products_path = app_configs["kz_pwp_products_path"]
    df = pd.read_csv(kz_pwp_products_path)
    df["device_names"] = df["device_names"].apply(lambda x: x.split(","))
    product_to_device = dict(zip(df["product_code"], df["device_names"]))
    return product_to_device


def docebo_indigo_categories():
    # Read the CSV file into a DataFrame
    indigo_service_category_path = app_configs["indigo_service_category_path"]

    df = pd.read_csv(indigo_service_category_path)

    # Convert the 'category_id' column to a list
    indigo_service_category = df["category_Id"].tolist()

    return indigo_service_category


class KaasAPIConfig:
    def __init__(self):
        self.domain_map = self.load_domain_map_from_csv()

    def get_print_fields(self):
        return (
            "documentID,title,contenttypeheader,product,contenttype,contentupdatedate,"
            "languagecode,disclosurelevel,store,description,renderlink,ishType,"
            "technicalLevel,productstagged,hpid"
        )

    def getlookup(self):
        look_path = app_configs["look_path"]
        df = pd.read_csv(look_path)
        df["id"] = df["id"].astype(str)
        lookup_dict = dict(zip(df["id"], df["name"]))
        return lookup_dict

    @staticmethod
    def load_domain_map_from_csv():
        # Read the CSV file into a DataFrame and ensure IDs are read as strings
        kaas_domain_map_path = app_configs["kaas_domain_map_path"]

        df = pd.read_csv(kaas_domain_map_path)
        df["product_id"] = df["product_id"].astype(str)
        # Convert the DataFrame back to a dictionary
        domain_map = dict(zip(df["product_id"], df["domain"]))
        return domain_map

    def get_domain_for_product(self, product_id):
        return self.domain_map.get(str(product_id), None)


def language_lookup():
    language_code_mapping = {i.name: i.value for i in LanguageEnum}
    additional_mapping = {
        "Simplified_Chinese": LanguageEnum.SimplifiedChinese.value,
        "Portuguese-Br": LanguageEnum.PortugueseBr.value,
        "Spanish_Latam": LanguageEnum.SpanishLatam.value,
        "Other Languages": LanguageEnum.Others.value,
        "EN": LanguageEnum.English.value,
        "En": LanguageEnum.English.value,
    }
    language_code_mapping.update(additional_mapping)

    return language_code_mapping


def find_all_devices(text):
    matches = []

    patterns_path = app_configs["patterns_path"]
    df_loaded = pd.read_csv(patterns_path)
    patterns = dict(zip(df_loaded["Device Name"], df_loaded["Pattern"]))
    compiled_patterns = {
        name: re.compile(pattern, re.IGNORECASE) for name, pattern in patterns.items()
    }
    for name, pattern in compiled_patterns.items():
        if pattern.search(text):  # Check for each match in the text
            matches.append(name)  # Add the name of the matched pattern to the list
    return (
        list(set(matches)) if matches else []
    )  # Return the list or None if no matches
