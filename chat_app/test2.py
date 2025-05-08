# import boto3
# import json
 
# secret_name = "dev/ks-daily/other"
# region_name = "us-west-2"
 
# # Create a Secrets Manager client
# session = boto3.Session(
#     aws_access_key_id="",
#     aws_secret_access_key=",
# )
 
# client = session.client(service_name="secretsmanager", region_name=region_name)
 
# try:
#     # Retrieve the secret value
#     response = client.get_secret_value(SecretId=secret_name)
 
#     if "SecretString" in response:
#         secret_data = json.loads(response["SecretString"])
#         kz_use_proxy = secret_data.get("KZ_USE_PROXY")  # Extract KZ_USE_PROXY
#         print(f"KZ_USE_PROXY: {kz_use_proxy}")
#     else:
#         print("SecretString not found in response.")
 
#     # Update the secret value
#     updated_secret_data = secret_data
#     updated_secret_data["KZ_USE_PROXY"] = "new_value"  # Example: Update KZ_USE_PROXY
 
#     # Update the secret in Secrets Manager
#     update_response = client.update_secret(
#         SecretId=secret_name, SecretString=json.dumps(updated_secret_data)
#     )
#     print(f"Secret updated successfully: {update_response}")
 
# except client.exceptions.ClientError as e:
#     print(f"Error retrieving or updating secret: {e}")

from langchain_core.documents import Document
import requests

from service.tool1 import access_token
# from ipython import embed


user_search_query='million impressions'
persona= 'engineer'
domain='indigo'
size=20
source='all'
language='en'
# @tool
def core_search():
    # query, state: Annotated[dict, InjectedState]):
    """this will communicate with search api and get response based on the query and filters given by user"""
    # print("State received by core_search:", state)  # Log the state for debugging
    # user_search_query = state.get("question", "")
    # domain = state.get("domain", "")
    # device = state.get("device", "")
    # persona = state.get("persona", "")
    # size = state.get("size", 20)
    # source = state.get("source", [])
    # language = state.get("language", "en")
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
        "source": source
    }
    print(params)
    response = requests.get(url, headers=headers, params=params, verify=False)
 
    result=response.json()
    open_docs = []
 
    for r in result['data']:
        metadata = {k: v for k, v in r.items() if k != "relevant_text"}
        open_docs.append(
            Document(
                page_content=r["relevant_text"],
                metadata=metadata
            )
        )
    return open_docs

r = core_search()

# embed()
print(r)
