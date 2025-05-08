import requests
from service.config import app_config
from service.config.env import environment

app_configs = app_config.AppConfig.get_all_configs()

def get_emb(input_text):
    "provide embeddigngs for given text"
    url = app_configs['ada_base_url']

    headers = {
        "api-key": environment.ADA_API_KEY,
        "Content-Type": "application/json"
    }
    data = {
        "input": input_text
    }
    
    response = requests.post(url, headers=headers, json=data)
    data=response.json()
    result=data['data'][0]['embedding']
    if response.status_code == 200:
        return result
    else:
        return None
    
# def generate_threat_embeddings():
#     """Generate and save ADA embeddings for threat queries"""
#     embeddings = []
#     threat_knowledge = {}
#     for query in THREAT_QUERIES:
#         query = query
#         emb = get_emb(query)
#         threat_knowledge[query]=emb
    
#     return threat_knowledge

# def get