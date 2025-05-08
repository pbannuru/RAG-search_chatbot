from opensearchpy import OpenSearch
from service.config.env import environment

from service.config import app_config
from sql_app.dbenums.core_enums import *
from utils.opensearch_utils import OpenSearchUtils

app_configs = app_config.AppConfig.get_all_configs()


class OpenSearchService:
    timeout_seconds = 160
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

    @staticmethod
    def generate_device_filter_for_hybrid_query(product_list: list):
        """
        Get device_filter for the query based on
        if the search query has any matching products
        from product_mapping.csv file
        """

        if product_list == []:
            return []
        elif len(product_list) > 1:
            return [
                {
                    "bool": {
                        "should": [
                            {"terms": {"metadata.products.keyword": product_list}},
                        ]
                    }
                }
            ]
        else:
            return [
                {
                    "bool": {
                        "should": [
                            {"match_phrase": {"metadata.products": product_list[0]}},
                        ]
                    }
                }
            ]


    @staticmethod
    def generate_persona_filter_for_query(persona: PersonaEnum):
        print(f'got input of persona as:::::::::::::::{persona},enum persona is::::::::{PersonaEnum.Engineer.name}')
        if persona == PersonaEnum.Engineer.name:
            return []
        else:
            return [{"match": {"metadata.persona": persona}}]

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
                    "fields": ["text"],
                }
            }
        ]
        return query_filter

    @staticmethod
    def generate_language_filter(language: LanguageEnum):
        return [{"term": {"metadata.language.keyword": "en"}}]
