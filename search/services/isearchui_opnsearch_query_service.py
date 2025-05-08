import ast
from typing import List
from sqlalchemy.orm import Session

from app.dto.core_search_response_model import (
    SearchResponse,
    SearchResponseData,
    SearchResponseMetadata,
)
from app.dto.isearchui_opensearch_query import (
    CreateOpenSearchQueryDto,
    UpdateOpenSearchNameDto,
    UpdateOpenSearchQueryDto,
)
from app.services.opensearch_service import OpenSearchService
from app.sql_app.dbenums.core_enums import DomainEnum, PersonaEnum, SourceEnum
from app.sql_app.dbmodels import isearchui_opensearch_query


class ISearchUIOpenSearchQueryService:
    __model = isearchui_opensearch_query.ISearchUIOpenSearchQueries

    def __init__(self, db: Session):
        self.db = db

    def create_opensearch_query(self, opensearch_query: CreateOpenSearchQueryDto):
        new_opensearch_query = self.__model(**opensearch_query.model_dump())
        new_opensearch_query.opensearch_query = """
# input: user_search_query, persona, domain, size, device
# output: opensearch_query

opensearch_query = {}
"""
        self.db.add(new_opensearch_query)
        self.db.commit()
        self.db.refresh(new_opensearch_query)
        return new_opensearch_query

    def get_all_opensearch_queries(self):
        queries = self.db.query(self.__model).all()
        return queries

    def get_one_opensearch_query(self, id: int):
        queries = self.db.query(self.__model).filter_by(id=id).one()
        return queries

    def delete_opensearch_queries(self, id: int):
        queries = self.db.query(self.__model).filter_by(id=id).delete()
        self.db.commit()
        return queries

    def update_opensearch_queries(
        self, id: int, opensearch_query: UpdateOpenSearchQueryDto
    ):
        self.db.query(self.__model).filter_by(id=id).update(
            opensearch_query.model_dump()
        )
        self.db.commit()
        return 1

    def update_opensearch_query_name(
        self, id: int, opensearch_query: UpdateOpenSearchNameDto
    ):
        self.db.query(self.__model).filter_by(id=id).update(
            opensearch_query.model_dump()
        )
        self.db.commit()
        return 1

    async def custom_search(
        self,
        opensearchquery_id: int,
        user_search_query: str,
        domain: DomainEnum,
        device: str,
        persona: PersonaEnum,
        size: int,
        source: List[SourceEnum],
    ):
        opensearchquery_item = self.get_one_opensearch_query(opensearchquery_id)
        local_namespace = {
            "opensearch_query": None,
            "size": size,
            "persona": persona.value,
            "device": device,
            "domain": domain.value,
            "user_search_query": user_search_query,
        }
        exec(opensearchquery_item.opensearch_query, {}, local_namespace)

        response = OpenSearchService.execute_custom_search(
            opensearch_query=local_namespace["opensearch_query"], source=source
        )

        search_data_list = []
        for search_hits in response["hits"]["hits"]:
            response_source = search_hits["_source"]
            response_source["score"] = search_hits["_score"]
            response_source["documentID"] = str(response_source["documentID"])
            search_data = SearchResponseData(**response_source)
            search_data_list.append(search_data)

        metadata_obj = SearchResponseMetadata(
            limit=size,
            size=len(search_data_list),
            query=user_search_query,
            device=device,
            persona=persona,
            domain=domain,
            source=source,
        )
        final_response = SearchResponse(metadata=metadata_obj, data=search_data_list)
        return final_response
