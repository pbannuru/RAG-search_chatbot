import requests
from utils.coreenum import *
from utils.opensearch_utils import *
from service.opensearchservice import OpenSearchService
from typing import Literal, List, Annotated
from opensearchpy import OpenSearch
from langgraph.prebuilt import InjectedState
from langchain_core.documents import Document
from langchain_core.tools import tool
from service.config.env import environment

app_configs = app_config.AppConfig.get_all_configs()

# def get_kaas_link(documentID):
#     import requests
#     url = 'https://kcs-dev.corp.hpicloud.net/api/v1/extras_kaas/render-links'
#     print(f"DocID ________________>{documentID}")
#     params = {
#         'documentID': documentID,
#         'language': 'en'
#     }
#     headers = {
#         'accept': 'application/json',
#         "Authorization": "Bearer " + access_token()
#         }
#     response = requests.get(url, headers=headers, params=params, verify=False)
#     result= response.json()
#     print(f"result---------------------------------->{result}")
#     render_link = result['data'][0]['render_link']
#     return render_link

# def get_bulk_renderlink(documentIDs):
#     """Fetches bulk render links for a list of document IDs."""
#     bulk_render_url = "https://css.api.hp.com/knowledge/v2/getRenderLinks"
#     access_token = get_access_token()  # Assuming this function exists
 
#     headers = {
#         "Content-Type": "application/json",
#         "Authorization": f"Bearer {access_token}",
#     }
 
#     data = {
#         "languageCode": "en",
#         "requests": [{"languageCode": "en", "ids": documentIDs}],
#     }
 
#     response = requests.post(bulk_render_url, headers=headers, json=data)
#     response.raise_for_status()
 
#     response_data = response.json()
#     render_links = {
#         i["id"]: i["renderLink"]
#         for i in response_data[0]["renderLinks"]
#         if "renderLink" in i
#     }
#     return render_links

def get_bulk_render_url_updated(documentIDs):
    """Fetch render links for a list of document IDs in bulk."""
    bulk_render_url = "https://css.api.hp.com/knowledge/v2/getRenderLinks"
    access_token = get_access_token()  # Ensure this function exists

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

    return renderlinks


def get_access_token():
    auth_url = 'https://css.api.hp.com/oauth/accesstoken'
    #'https://css.api.hp.com/knowledge/v2/generateEncryptedToken'
    auth_params = {
        'grant_type': 'client_credentials',
        'client_id': 'oVKELXf84JwfA1YKnAAAMt15mPs8T1BW',
        'client_secret': '0Pu6H8S1d5FqfEI1luFQYJpy6MP6t10Z'#'FGU4NRkV9GmCNIWuL3P7LITu5Jt7Tgg5' #'byf9T3wXXcCljGKcPAWxs9sxow4EAA2J'
    }
    try:
        response = requests.post(auth_url, data=auth_params)
        response.raise_for_status()
        auth_data = response.json()
        access_token = response.json()["access_token"]
        if access_token:
            return access_token
        else:
            print("Error: Access token not found in response.")
            return None
    except requests.exceptions.RequestException as e:
        print(f"Error in authentication request: {e}")
        return None
 
def access_token():
    url = 'https://login-itg.external.hp.com/as/token.oauth2'
 
    headers = {
        'Content-Type': 'application/x-www-form-urlencoded',
        'Cookie': 'HPIUIDITG=0LDlPLBnLGAYz4Lmwrgfck',
    }
 
    data = {
        'grant_type': 'client_credentials',
        'client_id': 'fCVyTLUc1C4yJwnfDSFdc0YMqlzxCrr7',
        'client_secret': 'gzjWw1GBah37dxueZM7CtytExqaNLNP4KNCXzQTDA5sDBx4gfKpNPMFY1jo7cE2v',
    }
 
    response = requests.post(url, headers=headers, data=data)
 
    if response.status_code == 200:
        return response.json().get('access_token')
    else:
        print(f"Failed to get token: {response.status_code}")
        print(response.text)
        return None
token= access_token()
 
 
@tool
def core_search(query, state: Annotated[dict, InjectedState]):
    """this will communicate with search api and get response based on the query and filters given by user"""
    # print("State received by core_search:", state)  # Log the state for debugging
    user_search_query = state.get("question", "")
    domain = state.get("domain", "")
    device = state.get("device", "")
    persona = state.get("persona", "")
    size = state.get("size", 20)
    source = state.get("source", [])
    language = state.get("language", "en")
    token = access_token()
    url = "https://kcs-dev.corp.hpicloud.net/api/v1/search"
    headers = {
        "accept": "application/json",
        "Authorization": "Bearer " + token
    }
    
    params = {
        "query": user_search_query,
        "domain": domain,
        "language": language,
        "persona": persona,
        "size": size,
        "source":str(source)
    }
    print(params)
    response = requests.get(url, headers=headers, params=params, verify=False)
    # print(f"response :_________________________{response.json()}")
    result=response.json()
    
    open_docs = []
    # return open_docs
    open_docs = []
    missing_renderlink_ids = [r["documentID"] for r in result['data'] if r.get("renderLink") is None]
    if missing_renderlink_ids:
        renderlink_mapping = get_bulk_render_url_updated(missing_renderlink_ids)
    for r in result['data']:
        if r.get("renderLink") is None:
            documentID = r["documentID"]
            if documentID in renderlink_mapping:
                r["renderLink"] = renderlink_mapping[documentID]
    for r in result['data']:
        metadata = {k: v for k, v in r.items() if k != "relevant_text"}

        open_docs.append(
            Document(
                page_content=r["relevant_text"],
                metadata=metadata
            )
        )
    return open_docs
