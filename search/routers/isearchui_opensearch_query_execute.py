from typing import Annotated, List
from fastapi import APIRouter, Depends, Path, Query

# from app.config.env import environment
from app.dto.core_search_response_model import SearchResponse
from app.middlewares.authentication import (
    JWTBearerTenantApiSwaggerAuthenticated,
)
from app.services.core_search_service import CoreSearchService
from app.services.isearchui_opnsearch_query_service import (
    ISearchUIOpenSearchQueryService,
)
from app.sql_app.database import get_db
from sqlalchemy.orm import Session

from app.sql_app.dbenums.core_enums import (
    DomainEnum,
    LanguageEnum,
    PersonaEnum,
    SourceEnum,
)


router = APIRouter(
    prefix="/isearchui_opensearch_query_execute",
    tags=["isearchui_opensearch_query_execute"],
)


@router.get(
    "/search/{id}",
    response_model=SearchResponse,
    # responses=response_example_search,
)
async def search(
    id: Annotated[int, Path()],
    query: Annotated[
        str,
        Query(
            max_length=256,
        ),
    ],
    domain: Annotated[DomainEnum, Query()],
    device: Annotated[
        str | None,
        Query(max_length=128),
    ] = None,
    language: Annotated[
        LanguageEnum, Query(description="Document language to search for")
    ] = LanguageEnum.English,
    persona: Annotated[PersonaEnum, Query()] = PersonaEnum.Operator,
    size: Annotated[
        int,
        Query(
            gt=0,
            le=50,
        ),
    ] = 50,
    source: Annotated[
        List[SourceEnum],
        Query(),
    ] = [SourceEnum.All],
    token_payload=Depends(JWTBearerTenantApiSwaggerAuthenticated()),
    db: Session = Depends(get_db),
) -> SearchResponse:
    if id == 0:
        return await CoreSearchService(None).search(
            query, domain, device, persona, size, source, language
        )

    else:
        return await ISearchUIOpenSearchQueryService(db).custom_search(
            id,
            domain=domain,
            device=device,
            persona=persona,
            user_search_query=query,
            size=size,
            source=source,
            # language=language,
        )
