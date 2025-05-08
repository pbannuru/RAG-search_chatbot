import traceback
from fastapi.exceptions import HTTPException
from requests import Session
from typing import Annotated, List
from fastapi import APIRouter, Depends, Query, Request
from app.config import app_config
from app.dto.core_search_response_model import SearchResponse
from app.middlewares.authentication import JWTBearerTenantApiSwaggerAuthenticated
from app.services.core_search_service_upgraded import CoreSearchService
from app.sql_app.database import get_db
from app.sql_app.dbenums.audit_log_enums import ContextEnum, ServiceEnum
from app.internal.utils.timer import Timer
from app.sql_app.dbmodels.core_tenant import CoreTenant
from app.sql_app.dbenums.core_enums import (
    PersonaEnum,
    DomainEnum,
    SourceEnum,
    LanguageEnum,
)
from pydantic import Field
from app.internal.utils.exception_examples import response_example_search
from app.internal.utils.api_rate_limiter import limiter

router = APIRouter(
    prefix="/search_upgraded",
    tags=["search_upgraded"],
)

app_configs = app_config.AppConfig.get_all_configs()
limiter_str = app_configs["search_limit"] + "/minute"


@router.get(
    "",
    summary="Search API for getting the data for the entered device matching the query",
    response_model=SearchResponse,
    responses=response_example_search,
)
@limiter.limit(limiter_str)
async def search_upgraded(
    request: Request,
    query: Annotated[
        str,
        Query(
            max_length=256,
            description="Query parameter to search",
        ),
    ],
    domain: Annotated[DomainEnum, Query(description="Data domain to be searched")],
    language: Annotated[
        LanguageEnum, Query(description="Document language to search for")
    ] = LanguageEnum.English,
    device: Annotated[
        str | None,
        Query(max_length=128, description="Device for which the query refers to"),
    ] = None,
    persona: Annotated[
        PersonaEnum, Query(description="Role of the user")
    ] = PersonaEnum.Operator,
    size: Annotated[
        int,
        Query(
            description="Maximum number of results to return.",
            gt=0,
            le=20,
        ),
    ] = 20,
    source: Annotated[
        List[SourceEnum],
        Query(
            description="Source to search from. All option searches all sources in the list."
        ),
    ] = [SourceEnum.All],
    token_payload=Depends(JWTBearerTenantApiSwaggerAuthenticated()),
) -> SearchResponse:
    """
    Retrieve items with a matching query parameter for the given device.

    Parameters:
    - `query` (str): Query parameter to search items.
    - `device` (str): Device for which the query refers to.
    - `size` (int): Maximum number of results to return.
    - `persona` (Enum): Role of the user - Operator/Engineer. (Set to Operator by default)
    - `domain` (Enum): Data domain to search
    - `source` (List[Enum]): Source to search from. (kaas, docebo, kz or all)
    - `language` (Enum): Document language to search for. Available language mapping  -
         English: en,
         Chinese: zh,
         French: fr,
         German: de,
         Japanese: ja,
         Korean: ko,
         Portuguese: pt,
         Russian: ru,
         Spanish: es,
         Italian: it,
         PortugueseBr: pt-BR,
         Hebrew: he,
         SpanishLatam: es-419,
         Hungarian: hu,
         Dutch: nl,
         SimplifiedChinese: zh-CN,
         Others: xx

    Returns:
    - Response items matching the query parameter.
      where `size` is maximum number of results to return and `limit` is number of results returned.
    """

    result = await CoreSearchService(None).search(
        query, domain, device, persona, size, source, language
    )
    return result
