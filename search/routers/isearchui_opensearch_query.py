from typing import Annotated, List
from fastapi import APIRouter, Depends, Path, Query, Request

# from app.config.env import environment
from app.dto.core_search_response_model import SearchResponse
from app.dto.isearchui_opensearch_query import (
    CreateOpenSearchQueryDto,
    UpdateOpenSearchNameDto,
    UpdateOpenSearchQueryDto,
)
from app.dto.isearchui_users import CreateUserDto
from app.middlewares.authentication import (
    JWTBearerISearchUserSwaggerAuthenticated,
    JWTBearerTenantApiSwaggerAuthenticated,
    VerifiedTokenBody,
)
from app.services.core_search_service import CoreSearchService
from app.services.isearchui_opnsearch_query_service import (
    ISearchUIOpenSearchQueryService,
)
from app.services.isearchui_users_service import ISearchUIUsersService
from app.sql_app.database import get_db
from sqlalchemy.orm import Session

from app.sql_app.dbenums.core_enums import DomainEnum, PersonaEnum, SourceEnum


router = APIRouter(
    prefix="/isearchui_opensearch_query",
    tags=["isearchui_opensearch_query"],
)


@router.post("/")
async def create_opensearch_query(
    opensearch_query: CreateOpenSearchQueryDto,
    dependencies=Depends(JWTBearerISearchUserSwaggerAuthenticated()),
    db: Session = Depends(get_db),
):
    return ISearchUIOpenSearchQueryService(db).create_opensearch_query(opensearch_query)


@router.get("/")
async def get_opensearch_queries(
    dependencies=Depends(JWTBearerISearchUserSwaggerAuthenticated()),
    db: Session = Depends(get_db),
):
    return ISearchUIOpenSearchQueryService(db).get_all_opensearch_queries()


@router.patch("/name/{id}")
async def update_opensearch_query(
    id: Annotated[int, Path()],
    update_name: UpdateOpenSearchNameDto,
    dependencies=Depends(JWTBearerISearchUserSwaggerAuthenticated()),
    db: Session = Depends(get_db),
):
    return ISearchUIOpenSearchQueryService(db).update_opensearch_query_name(
        id, update_name
    )


@router.patch("/{id}")
async def update_opensearch_query(
    id: Annotated[int, Path()],
    update_query: UpdateOpenSearchQueryDto,
    dependencies=Depends(JWTBearerISearchUserSwaggerAuthenticated()),
    db: Session = Depends(get_db),
):
    return ISearchUIOpenSearchQueryService(db).update_opensearch_queries(
        id, update_query
    )


@router.get("/{id}")
async def get_one_opensearch_query(
    id: Annotated[int, Path()],
    dependencies=Depends(JWTBearerISearchUserSwaggerAuthenticated()),
    db: Session = Depends(get_db),
):
    return ISearchUIOpenSearchQueryService(db).get_one_opensearch_query(id)


@router.delete("/{id}")
async def delete_opensearch_query(
    id: Annotated[int, Path()],
    dependencies=Depends(JWTBearerISearchUserSwaggerAuthenticated()),
    db: Session = Depends(get_db),
):
    return ISearchUIOpenSearchQueryService(db).delete_opensearch_queries(id)
