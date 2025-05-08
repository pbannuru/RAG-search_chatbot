# 

from typing import List
from app.internal.utils.timer import Timer
from app.internal.utils.opensearch_utils import *
from app.services.opensearch_service_upgraded_api import OpenSearchService
from app.dto.core_search_response_model import *
from app.sql_app.dbenums.core_enums import (
    PersonaEnum,
    DomainEnum,
    SourceEnum,
    LanguageEnum,
)


class CoreSearchService:

    def __init__(self, db=None):
        self.db = db

    async def search(
        self,
        query: str,
        domain: DomainEnum,
        device: str,
        persona: PersonaEnum,
        size: int,
        source: List[SourceEnum],
        language: LanguageEnum,
    ):

        timer = Timer().start_timer()
        response = OpenSearchService.get_search_response(
            query, domain, device, persona, size, source, language
        )
        timer.end_timer()

        # search_start_time_str = timer.strftime("%Y-%m-%d %H:%M:%S")
        OpenSearchService.log_search_response(
            query,
            domain,
            device,
            persona,
            source,
            language,
            timer.start_time_string,
            timer.elapsed_time_ms,
        )
        acronym_dict=OpenSearchUtilsData.acronym_dict

        search_data_list = []
        for search_hits in response["hits"]["hits"]:
            if search_hits["_score"] >= 0.3:
                response_source = search_hits["_source"]
                full_text = response_source.get("text", "")
                relevant_text=OpenSearchUtils.extract_relevant_text_with_acronyms(query, full_text, acronym_dict, limit=3)
                response_source["score"] = search_hits["_score"]
                response_source["documentID"] = str(response_source["metadata"]["documentID"])
                response_source["title"] = response_source["metadata"]["title"]
                response_source["description"] = response_source["metadata"]["description"]
                response_source["contentType"] = response_source["metadata"]["contentType"]
                response_source["contentUpdateDate"] = response_source["metadata"]["contentUpdateDate"]
                response_source["language"] = response_source["metadata"]["language"]
                response_source["renderLink"] = response_source["metadata"]["renderLink"]
                response_source['relevant_text']= response_source.get("text", "")
                response_source['products']= response_source["metadata"]["products"]
                search_data = SearchResponseData(**response_source)
                search_data_list.append(search_data)

        metadata_obj = SearchResponseMetadata(
            limit=size,
            size=len(search_data_list),
            query=query,
            device=device,
            persona=persona,
            domain=domain,
            source=source,
            language=language,
        )
        final_response = SearchResponse(metadata=metadata_obj, data=search_data_list)
        return final_response
    