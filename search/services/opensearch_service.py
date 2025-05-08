import re
from opensearchpy import OpenSearch
from app.config import app_config
import logging
from app.config.env import environment
from app.sql_app.dbenums.core_enums import (
    PersonaEnum,
    DomainEnum,
    SourceEnum,
    LanguageEnum,
)
from app.internal.utils.opensearch_utils import OpenSearchUtils

app_configs = app_config.AppConfig.get_all_configs()
index_configs = app_config.AppConfig.get_sectionwise_configs("index_values")


class OpenSearchService:

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

    ################ FILTERS FOR HYBRID QUERY ################
    @staticmethod
    def generate_device_filter_for_hybrid_query(
        device: str | None, user_search_query: str, domain: DomainEnum, query_without_product_keyword: str
    ):
        """
        Get device_filter for the query based on
        if the search query has any matching products
        from product_mapping.csv file
        """
        product_mapping = OpenSearchUtils.get_product_mapping(domain)
        modified_search_query = OpenSearchUtils.remove_unpaired_doublequotes_from_query(
            user_search_query
        )
        query_without_product_keyword_and_unpaired_quotes = OpenSearchUtils.remove_unpaired_doublequotes_from_query(
            query_without_product_keyword
        )
        if device is None:
            for key, device_list in product_mapping.items():
                if f" {key} " in f" {modified_search_query} ":
                    return [
                        {
                            "bool": {
                                "should": [
                                    {
                                        "bool": {
                                            "must_not": [
                                                {"exists": {"field": "products"}}
                                            ]
                                        }
                                    },
                                    {"terms": {"products.keyword": device_list}},
                                ]
                            }
                        }
                    ], query_without_product_keyword_and_unpaired_quotes
            return [], query_without_product_keyword_and_unpaired_quotes  # Return an empty list if no match is found

        return [
            {
                "bool": {
                    "should": [
                        {"bool": {"must_not": [{"exists": {"field": "products"}}]}},
                        {"match_phrase": {"products": device}},
                    ]
                }
            }
        ], query_without_product_keyword_and_unpaired_quotes

    @staticmethod
    def generate_persona_filter_for_query(persona: PersonaEnum):
        if persona == PersonaEnum.Engineer:
            return []
        else:
            return [{"match": {"persona": persona.value}}]

    @staticmethod
    def generate_exact_match_query_filter(user_search_query: str):
        """
        Get `query_filter` If the `user search query`
        has pair(s) of double quote(s) to get the exact match results.
        """
        # If search query has no double quotes, No 'query_filter' is been used.
        if '"' not in user_search_query:
            return []
        modified_search_query = OpenSearchUtils.remove_unpaired_doublequotes_from_query(
            user_search_query
        )
        query_filter = [
            {
                "query_string": {
                    "query": modified_search_query,
                    "fields": ["ti_desc_prod"],
                }
            }
        ]
        return query_filter

    @staticmethod
    def generate_language_filter(language: LanguageEnum):
        return [{"term": {"language.keyword": language.value}}]

    ################ OPENSEARCH HYBRID QUERY ################
    @staticmethod
    def get_search_query(
        user_search_query: str,
        domain: DomainEnum,
        device: str,
        persona: PersonaEnum,
        size: int,
        language: LanguageEnum,
        query_without_product_keyword: str
    ):

        persona_filter = OpenSearchService.generate_persona_filter_for_query(persona)
        query_filter = OpenSearchService.generate_exact_match_query_filter(
            query_without_product_keyword
        )
        device_filter, query_without_product_keywords = OpenSearchService.generate_device_filter_for_hybrid_query(
            device, user_search_query, domain, query_without_product_keyword
        )
        language_filter = OpenSearchService.generate_language_filter(language)
        open_search_query = {
            "size": size,
            "_source": {
                "exclude": [
                    "body_embedding",
                    "_score",
                    "query_embedding",
                    "title_embedding",
                    "desc_embedding",
                ]
            },
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
                                        "query": query_without_product_keywords,
                                        "minimum_should_match": "66%",
                                        "type": "most_fields",
                                        "fuzziness": "auto",
                                        "fields": [
                                            "title^7",
                                            "ti_desc_prod"
                                        ],
                                        "boost": 7
                                        }
                                    },
                                    "functions": [
                                        {
                                        "gauss": {
                                            "contentUpdateDate": {
                                            "origin": "now",
                                            "scale": "2190d",
                                            "decay": 0.9
                                            }
                                        },
                                        "weight": 2
                                        }
                                    ],
                                    "score_mode": "multiply"
                                    }
                                },
                                {
                                    "function_score": {
                                    "query": {
                                        "multi_match": {
                                        "query": query_without_product_keywords,
                                        "minimum_should_match": "66%",
                                        "type": "most_fields",
                                        "fields": [
                                            "title^2",
                                            "ti_desc_prod^3"
                                        ],
                                        "analyzer": "word_join_analyzer",
                                        "boost": 9
                                        }
                                    },
                                    "functions": [
                                        {
                                        "gauss": {
                                            "contentUpdateDate": {
                                            "origin": "now",
                                            "scale": "2190d",
                                            "decay": 0.9
                                            }
                                        },
                                        "weight": 2
                                        }
                                    ],
                                    "score_mode": "multiply"
                                    }
                                },
                                {
                                    "function_score": {
                                    "query": {
                                        "multi_match": {
                                        "query": query_without_product_keywords,
                                        "type": "phrase",
                                        "fields": [
                                            "title^2",
                                            "ti_desc_prod"
                                        ],
                                        "boost": 4,
                                        "analyzer": "acronym_synonym_analyzer"
                                        }
                                    },
                                    "functions": [
                                        {
                                        "gauss": {
                                            "contentUpdateDate": {
                                            "origin": "now",
                                            "scale": "2190d",
                                            "decay": 0.9
                                            }
                                        },
                                        "weight": 2
                                        }
                                    ],
                                    "score_mode": "multiply"
                                    }
                                },
                                {
                                    "function_score": {
                                    "query": {
                                        "multi_match": {
                                        "query": query_without_product_keywords,
                                        "type": "bool_prefix",
                                        "minimum_should_match": "66%",
                                        "fields": [
                                            "ti_desc_prod._index_prefix^3",
                                            "ti_desc_prod"
                                        ],
                                        "boost": 6
                                        }
                                    },
                                    "functions": [
                                        {
                                        "gauss": {
                                            "contentUpdateDate": {
                                            "origin": "now",
                                            "scale": "2190d",
                                            "decay": 0.9
                                            }
                                        },
                                        "weight": 2
                                        }
                                    ],
                                    "score_mode": "multiply"
                                    }
                                }
                            ],
                                "filter": [
                                    *persona_filter,
                                    *language_filter,
                                    *device_filter,
                                    *query_filter,
                                    {"match": {"Domain": domain.value}},
                                    {"exists": {"field": "Doc_Status"}},
                                    {"term": {"Doc_Status.keyword": "published"}},
                                ],
                            }
                        },
                        {
                            "neural": {
                                "query_embedding": {
                                    "query_text": query_without_product_keywords,
                                    "model_id": app_configs["model_id"],
                                    "k": 100,
                                    "filter": {
                                        "bool": {
                                            "must": [],
                                            "filter": [
                                                *persona_filter,
                                                *language_filter,
                                                *device_filter,
                                                *query_filter,
                                                {"match": {"Domain": domain.value}},
                                                {"exists": {"field": "Doc_Status"}},
                                                {
                                                    "term": {
                                                        "Doc_Status.keyword": "published"
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
        }
        return open_search_query

    ################ OPENSEARCH TEMPLATE QUERY ################
    @staticmethod
    def get_search_template_query(
        query_without_stop_words: str,
        domain: DomainEnum,
        device: str,
        persona: PersonaEnum,
        size: int,
        language: LanguageEnum,
        query_without_product_keyword: str
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
            "id": app_configs["search_template"],
            "params": {
                "limit": True,
                "size": size,
                "domain": domain.value,
                "language": language.value,
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
            opensearch_template_query["params"]["exact_match"] = True

        products, search_query_without_product_key = (
            OpenSearchUtils.get_devices_from_query(
                device, doublequote_modified_search_query, domain, query_without_product_keyword
            )
        )
        opensearch_template_query["params"]["query"] = search_query_without_product_key
        if len(products) >= 1:
            opensearch_template_query["params"]["hasProducts"] = True
            opensearch_template_query["params"]["products"] = products

        if len(search_query_without_product_key.split()) == 2:
            two_words = True
        else:
            two_words = False
        opensearch_template_query["params"]["two_words"] = two_words
        return opensearch_template_query

    @staticmethod
    def get_search_response(
        user_search_query: str,
        domain: DomainEnum,
        device: str,
        persona: PersonaEnum,
        size: int,
        source: list[SourceEnum],
        language: LanguageEnum,
    ):
        """
        Returns the response to opensearch query
        """

        source_list = [source_item.value for source_item in source]
        indices = [index_configs[source_name] for source_name in set(source_list)]
        # If there are any stop words in `user_search_query` - Remove.
        user_search_query_lower = user_search_query.lower()
        query_without_stop_words = OpenSearchUtils.remove_stop_words(
            user_search_query_lower
        )
        query_without_unpaired_quotes = OpenSearchUtils.remove_unpaired_doublequotes_from_query(query_without_stop_words)
        query_without_product_keyword = OpenSearchUtils.remove_product_keyword_from_search_query(query_without_unpaired_quotes, domain)

        if len(query_without_product_keyword.split()) <= 2:
            request_body = OpenSearchService.get_search_template_query(
                query_without_stop_words, domain, device, persona, size, language, query_without_product_keyword
            )
            return OpenSearchService.client.search_template(
                body=request_body, index=indices
            )
        else:
            request_body = OpenSearchService.get_search_query(
                query_without_stop_words, domain, device, persona, size, language, query_without_product_keyword
            )
            return OpenSearchService.client.search(
                index=indices,
                params={"search_pipeline": app_configs["pipeline"]},
                body=request_body,
            )

    @staticmethod
    def execute_custom_search(
        opensearch_query: str,
        source: list[SourceEnum],
    ):
        """
        Returns the response to opensearch query
        """
        request_body = opensearch_query
        source_list = [source_item.value for source_item in source]
        indices = [index_configs[source_name] for source_name in set(source_list)]
        return OpenSearchService.client.search(
            index=indices,
            params={"search_pipeline": app_configs["pipeline"]},
            body=request_body,
        )

    ################ Auto suggest ################

    def get_auto_suggest_query(
        auto_suggest_term: str,
        device: str,
        persona: PersonaEnum,
        size: int,
        domain: DomainEnum,
        language: LanguageEnum,
    ):
        auto_suggest_query = {
            "id": app_configs["template"],
            "params": {
                "search_word": auto_suggest_term,
                "limit": size,
                "products": device,
                "domain": domain.value,
                "language": language.value,
            },
        }
        # If person is engineer we don't send any value. This will get results for all personas.
        # Only for `Operator`, we specify value to filter only `Operator` documents.
        if persona != PersonaEnum.Engineer:
            auto_suggest_query["params"].update({"persona": persona.value})
        return auto_suggest_query

    def get_auto_suggest_response(
        user_search_query: str,
        device: str,
        persona: PersonaEnum,
        size: int,
        domain: DomainEnum,
        source: list[SourceEnum],
        language: LanguageEnum,
    ):
        """
        Returns the response to opensearch auto suggest query
        """
        request_query = OpenSearchService.get_auto_suggest_query(
            user_search_query, device, persona, size, domain, language
        )
        source_list = [source_item.value for source_item in source]
        indices = [index_configs[source_name] for source_name in set(source_list)]

        return OpenSearchService.client.search_template(
            body=request_query, index=indices
        )

    ################ Logs response details to index ################
    @staticmethod
    def log_search_response(
        user_search_query: str,
        domain: DomainEnum,
        device: str,
        persona: PersonaEnum,
        source: list[SourceEnum],
        language: LanguageEnum,
        start_time: str,
        timetaken: float,
    ):
        """
        Logs the response to opensearch with given details
        """
        # Combining query parameters with timestamp
        data_to_log_index = {
            "query": user_search_query,
            "domain": domain.value,
            "device": device,
            "persona": persona.value,
            "source": [source_item.value for source_item in source],
            "language": language.value,
            "timestamp": start_time,
            "timetaken": timetaken,
        }

        # Indexing data into 'kcss-v7' index
        logging_response = OpenSearchService.client.index(
            index=app_configs["log_index"], body=data_to_log_index
        )
        if environment.DEBUG_MODE:
            print("logging_response:", logging_response)
        return logging_response
