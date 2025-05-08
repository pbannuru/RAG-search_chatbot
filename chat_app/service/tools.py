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

client = OpenSearch(
    hosts=[
        {
            "host": app_configs["host"],
            "port": app_configs["port"],
        }
    ],
    http_auth=(
        app_configs["opensearch_auth_user"],
        environment.AUTH_OPENSEARCH_PASSWORD,
    ),
    use_ssl=eval(app_configs["use_ssl"]),
    verify_certs=eval(app_configs["verify_certs"]),
    ssl_assert_hostname=eval(app_configs["ssl_assert_hostname"]),
    ssl_show_warn=eval(app_configs["ssl_show_warn"]),
)

def get_search_template_query(
    query_without_stop_words: str,
    domain: DomainEnum,
    device: str,
    persona: PersonaEnum,
    size: int,
    language: LanguageEnum,
):
    """
    Fucntion to prepare template based opensearch query to support catalogID/ErrorCode
    search. Below are the scenarios handled:
    - Any search query having two or less words in it, uses `opensearch_template_query`.
    - Opensearch query expects `persona` to be added only when It's `operator`.
    - `exact_match` flag has to be set If there are any paired double quotes in search query.
    - User search query has to be trimmed If It contains any product keywords; and
        matched devices from product mapping dictionary have to be passed to `products` field in query.
        ex: `CA593-00000 12000` will be split into `query`: CA593-00000, `products`: ['HP Indigo 12000 Digital Press', 'HP Indigo 12000HD Digital Press']
    """
    opensearch_template_query = {
        "id": "lexical_search_template_v2",  # app_configs["search_template"],
        "params": {
            "limit": True,
            "size": size,
            "domain": domain,
            "language": "en",
        },
    }

    # Update the template query dictionary based on the scenarios mentioned in docstring.
    if persona == PersonaEnum.Operator:
        opensearch_template_query["params"]["persona"] = persona.value

    doublequote_modified_search_query = (
        OpenSearchUtils.remove_unpaired_doublequotes_from_query(
            query_without_stop_words
        )
    )
    if '"' in doublequote_modified_search_query:
        opensearch_template_query["params"]["exact_match"] = False

    products, search_query_without_product_key = OpenSearchUtils.get_devices_from_query(
        device, doublequote_modified_search_query, domain
    )
    opensearch_template_query["params"]["query"] = search_query_without_product_key
    if len(products) >= 1:
        opensearch_template_query["params"]["hasProducts"] = True
        opensearch_template_query["params"]["products"] = products

    if len(search_query_without_product_key.split()) >= 2:
        two_words = True
    else:
        two_words = False
    opensearch_template_query["params"]["two_words"] = two_words
    return opensearch_template_query


@tool
def BM25(query, state: Annotated[dict, InjectedState]):
    """
    Returns the response to opensearch query if it is one word or 2 word search
    """
    print("State received by BM25:", state)  # Log the state for debugging
    user_search_query = state.get("question", "")
    domain = state.get("domain", "")
    device = state.get("device", "")
    persona = state.get("persona", "")
    size = state.get("size", 10)
    source = state.get("source", [])
    language = state.get("language", "en")
    print(
        f"Extracted arguments: query={user_search_query}, domain={domain}, device={device}, size={size}, source={source}, language={language}"
    )
    # If there are any stop words in `user_search_query` - Remove.
    user_search_query_lower = user_search_query.lower()
    query_without_stop_words = OpenSearchUtils.remove_stop_words(
        user_search_query_lower
    )

    request_body = get_search_template_query(
        query_without_stop_words, domain, device, persona, size, language
    )
    documents = client.search_template(body=request_body, index=source)
    print("BM25 Request Body")
    print(request_body)
    # print("Docs in retrice_mmr")
    open_docs = []
    kaas_index_ids={}
    count=0
    for r in documents["hits"]["hits"]:
        # score=retrieval_grader.invoke({"question": query, "document": r["_source"]["text"]})
        if r["_score"]>0.3:
            print(r["_source"]["metadata"]["renderLink"])
            count=count+1
            kaas_render_link =app_configs['extras_kaas_render_url']
            if 'kaas' in r["_index"]:
                 r["_source"]["metadata"]["renderLink"] = kaas_render_link + r["_source"]["metadata"]["documentID"]
                #  r["_source"]["metadata"]["renderLink"]="https://kcs-dev.corp.hpicloud.net/api/v1/extras_kaas/render_url?documentID="+r["_source"]["metadata"]["documentID"]
            metadata=r["_source"]["metadata"]
            metadata["search_score"] = r["_score"]
            open_docs.append(
                Document(
                    page_content=r["_source"]["text"], metadata=metadata
                )
            )
        # print("Docs in retrice_mmr")
        state["rows"]=count
    return open_docs


def prepare_user_search_query(user_search_query: str):
    query_without_stop_words = OpenSearchUtils.remove_stop_words(user_search_query)
    query_without_unpaired_quotes = (
        OpenSearchUtils.remove_unpaired_doublequotes_from_query(
            query_without_stop_words
        )
    )
    return query_without_unpaired_quotes

@tool
def Scemantic(query, state: Annotated[dict, InjectedState]):
    """this takes full neural search when query is more than 2 words this will come in action"""
    # print("State received by Scemantic:", state)  # Log the state for debugging
    user_search_query = state.get("question", "")
    domain = state.get("domain", "")
    device = state.get("device", "")
    persona = state.get("persona", "")
    size = state.get("size", 10)
    source = state.get("source", [])
    language = state.get("language", "en")

    """this takes full neural search when query is more than 2 words this will come in action"""
    persona_filter = OpenSearchService.generate_persona_filter_for_query(persona)
    print(f"obtained_filter:::::::::::::::::::::::{persona_filter}")
    query_without_unpaired_quotes_and_stopword = prepare_user_search_query(
        user_search_query.lower()
    )
    product_list, query_without_product_key = OpenSearchUtils.get_devices_from_query(
        device, query_without_unpaired_quotes_and_stopword, domain
    )
    query_filter = OpenSearchService.generate_exact_match_query_filter(
        query_without_product_key
    )
    device_filter = OpenSearchService.generate_device_filter_for_hybrid_query(
        product_list
    )
    print('---------------',device_filter)
    language_filter = OpenSearchService.generate_language_filter(language)


    query = {
        "size": size,
        "_source": {"excludes": ["vector_field"]},
        "query": {
            "hybrid": {
                "queries": [
                    {
                        "bool": {
                            "should": [
                                {
                                    "function_score": {
                                        "query": {
                                            "multi_match": {
                                                "query": query_without_product_key,
                                                "minimum_should_match": "66%",
                                                "type": "most_fields",
                                                "fuzziness": "auto",
                                                "fields": ["metadata.title^7", "text"],
                                                "boost": 7,
                                            }
                                        },
                                        "functions": [
                                            {
                                                "gauss": {
                                                    "metadata.contentUpdateDate": {
                                                        "origin": "now",
                                                        "scale": "2190d",
                                                        "decay": 0.9,
                                                    }
                                                },
                                                "weight": 2,
                                            }
                                        ],
                                        "score_mode": "multiply",
                                    }
                                },
                                {
                                    "function_score": {
                                        "query": {
                                            "multi_match": {
                                                "query": query_without_product_key,
                                                "minimum_should_match": "66%",
                                                "type": "most_fields",
                                                "fields": [
                                                    "metadata.title^2",
                                                    "text^3",
                                                ],
                                                "analyzer": "word_join_analyzer",
                                                "boost": 9,
                                            }
                                        },
                                        "functions": [
                                            {
                                                "gauss": {
                                                    "metadata.contentUpdateDate": {
                                                        "origin": "now",
                                                        "scale": "2190d",
                                                        "decay": 0.9,
                                                    }
                                                },
                                                "weight": 2,
                                            }
                                        ],
                                        "score_mode": "multiply",
                                    }
                                },
                                {
                                    "function_score": {
                                        "query": {
                                            "multi_match": {
                                                "query": query_without_product_key,
                                                "type": "phrase",
                                                "fields": [".metadata.title^2", "text"],
                                                "boost": 4,
                                                "analyzer": "acronym_synonym_analyzer",
                                            }
                                        },
                                        "functions": [
                                            {
                                                "gauss": {
                                                    "metadata.contentUpdateDate": {
                                                        "origin": "now",
                                                        "scale": "2190d",
                                                        "decay": 0.9,
                                                    }
                                                },
                                                "weight": 2,
                                            }
                                        ],
                                        "score_mode": "multiply",
                                    }
                                },
                                {
                                    "function_score": {
                                        "query": {
                                            "multi_match": {
                                                "query": query_without_product_key,
                                                "type": "bool_prefix",
                                                "minimum_should_match": "66%",
                                                "fields": ["text^3"],
                                                "boost": 6,
                                            }
                                        },
                                        "functions": [
                                            {
                                                "gauss": {
                                                    "metadata.contentUpdateDate": {
                                                        "origin": "now",
                                                        "scale": "2190d",
                                                        "decay": 0.9,
                                                    }
                                                },
                                                "weight": 2,
                                            }
                                        ],
                                        "score_mode": "multiply",
                                    }
                                },
                            ],
                            "filter": [
                                *persona_filter,
                                *language_filter,
                                *device_filter,
                                {"match": {"metadata.Domain": domain}},
                                {"exists": {"field": "metadata.Doc_Status"}},
                                {"term": {"metadata.Doc_Status.keyword": "published"}},
                            ],
                        }
                    },
                    {
                        "neural": {
                            "vector_field": {
                                "query_text": query_without_product_key,
                                "model_id": app_configs['model_id'],
                                "k": 100,
                                "filter": {
                                    "bool": {
                                        "must": [],
                                        "filter": [
                                            *persona_filter,
                                            *language_filter,
                                            *device_filter,
                                            {"match": {"metadata.Domain": domain}},
                                            {
                                                "exists": {
                                                    "field": "metadata.Doc_Status"
                                                }
                                            },
                                            {
                                                "term": {
                                                    "metadata.Doc_Status.keyword": "published"
                                                }
                                            },
                                        ],
                                    }
                                },
                            }
                        }
                    },
                ]
            }
        },
        "ext": {"rerank": {"query_context": {"query_text": query_without_product_key}}},
    }
    print("-------------------------Neural search query----------------------", query)
    source_list = [source_item for source_item in source]
    indices = source_list
    print(indices)
    # print(query)
    documents = client.search(
        body=query,
        index=indices,
        # search_pipeline="ph2_search_pipeline",
        search_pipeline=app_configs['pipeline']  #"ph2_search_rerank_pipeline"
    )

    # client.search
    print("Docs in retrice_mmr")
    open_docs = []
    kaas_index_ids=[]
    count = 0
    for r in documents["hits"]["hits"]:
        # score=retrieval_grader.invoke({"question": query, "document": r["_source"]["text"]})
        if r["_score"] > 0.3:
            print(r["_source"]["metadata"]["renderLink"])
            count = count + 1
            kaas_render_link =app_configs['extras_kaas_render_url']
            if 'kaas' in r["_index"]:
                 r["_source"]["metadata"]["renderLink"] = kaas_render_link + r["_source"]["metadata"]["documentID"]

            metadata=r["_source"]["metadata"]
            metadata["search_score"] = r["_score"]
            open_docs.append(
                Document(
                    page_content=r["_source"]["text"], metadata=metadata
                )
            )
        # print("Docs in retrice_mmr")
        state["rows"] = count

    return open_docs
