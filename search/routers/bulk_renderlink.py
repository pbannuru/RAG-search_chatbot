from typing import Annotated
from fastapi import APIRouter, Depends, Query, Request
from app.config import app_config
from app.middlewares.authentication import JWTBearerTenantApiSwaggerAuthenticated
from app.sql_app.dbenums.core_enums import LanguageEnum
from app.sql_app.dbmodels.core_tenant import CoreTenant
from app.services.bulk_renderlink_service import BulkRenderLinkService
from app.internal.utils.exception_examples import response_examples_bulk
from app.dto.bulk_renderlink_response import BulkRenderLinkResponse
from app.internal.utils.api_rate_limiter import limiter

router = APIRouter(
    prefix="/extras_kaas",
    tags=["render-links"],
)

app_configs = app_config.AppConfig.get_all_configs()
limiter_str = app_configs["bulk_renderlink_limit"] + "/minute"


@router.get(
    "/render-links",
    summary="extras_kaas API to generate list of render links for given list of documentIDs",
    response_model=BulkRenderLinkResponse,
    responses=response_examples_bulk,
)
@limiter.limit(limiter_str)
async def render_url(
    request: Request,
    documentID: Annotated[
        list[str],
        Query(
            max_length=50,
            description="list of IDs of the documents for which the render link URL needs to be created",
        ),
    ] = [],
    language: Annotated[
        LanguageEnum, Query(description="Document language to search for")
    ] = LanguageEnum.English,
    token_payload: CoreTenant = Depends(JWTBearerTenantApiSwaggerAuthenticated()),
) -> BulkRenderLinkResponse:
    """
    Generates render link URL for the given document ID

    Parameters:
    `documentID`: (list of str) IDs of the documents for which the render link URL need to be created. (ish_ / pdf_)
    `language`: (str) Document language to search for.

    Returns:
    A list of documentIDs and render link URL, status messages.
    """
    result = await BulkRenderLinkService(None).renderlink(documentID, language)
    return result
