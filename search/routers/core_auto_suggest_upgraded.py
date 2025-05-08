from fastapi import APIRouter, Depends, Query, Request
from app.middlewares.authentication import JWTBearerTenantApiSwaggerAuthenticated
from app.services.core_auto_suggest_service_upgraded_api import CoreAutoSuggestService
from app.sql_app.database import get_db
from sqlalchemy.orm import Session
from app.dto.autosuggest import AutoSuggestResponse
from app.sql_app.dbenums.core_enums import (
    LanguageEnum,
    PersonaEnum,
    DomainEnum,
    SourceEnum,
)
from typing import Annotated, List
from pydantic import Field
from app.sql_app.dbmodels.core_tenant import CoreTenant
from app.internal.utils.exception_examples import response_example_autosuggest
from app.internal.utils.api_rate_limiter import limiter
from app.config import app_config

router = APIRouter(
    prefix="/suggest_upgraded",
    tags=["suggest_upgraded"],
)

app_configs = app_config.AppConfig.get_all_configs()
limiter_str = app_configs["suggest_limit"] + "/minute"


@router.get(
    "",
    summary="Auto-suggestion API to retrive auto suggestions based on user inputs",
    response_model=AutoSuggestResponse,
    responses=response_example_autosuggest,
)
@limiter.limit(limiter_str)
async def auto_suggest(
    request: Request,
    query: Annotated[
        str,
        Query(
            max_length=256,
            description="The input query for which suggestions are requested.",
        ),
    ],
    domain: Annotated[DomainEnum, Query(description="Data domain to be searched")],
    limit: Annotated[
        int,
        Query(
            description="Maximum number of results to return. Maximum supported size is 15.",
            gt=0,
            le=15,
        ),
    ] = 10,
    device: Annotated[
        str | None,
        Query(max_length=128, description="Device for which the query refers to."),
    ] = None,
    persona: Annotated[
        PersonaEnum, Query(description="Role of the user")
    ] = PersonaEnum.Operator,
    source: Annotated[
        List[SourceEnum],
        Query(
            description="Source to search from. All option searches all sources in the list."
        ),
    ] = [SourceEnum.All],
    language: Annotated[
        LanguageEnum, Query(description="Document language to search for")
    ] = LanguageEnum.English,
    token_payload: CoreTenant = Depends(JWTBearerTenantApiSwaggerAuthenticated()),
    db: Session = Depends(get_db),
) -> AutoSuggestResponse:
    """
    Retrieve auto-suggestions based on the provided query.

    Parameters:
    - `query` (str): Query parameter to search items.
    - `device` (str): Device for which the query refers to. It is not mandatory parameter
    - `limit` (int): Maximum number of results to return. Set to 10 by default and the maximum supported limit is 15.
    - `persona` (Enum): Role of the user - Operator/Engineer. (Set to Operator by default)
    - `domain` (Enum): Data domain to search
    - `source` (list[Enum]): Source to search from.
    - `language` (Enum): Document language to search for.

    Returns:
    - List of suggested items matching the provided query.
      where `limit` is maximum number of results to return and `size` is number of results returned.

    """

    result = await CoreAutoSuggestService(db).auto_suggest(
        query, persona, limit, domain, device, source, language
    )
    return result
