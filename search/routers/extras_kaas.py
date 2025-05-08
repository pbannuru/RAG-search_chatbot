from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException, Query, Request
from fastapi.exceptions import HTTPException
from pydantic import Field
from app.config import app_config
from app.dto.render_link_response import RenderLinkResponse
from app.middlewares.authentication import JWTBearerTenantApiSwaggerAuthenticated
from app.sql_app.dbmodels.core_tenant import CoreTenant
from app.services.extras_kaas_service import RenderLinkService
from app.internal.utils.exception_examples import response_examples_extras
from app.internal.utils.api_rate_limiter import limiter

router = APIRouter(
    prefix="/extras_kaas",
    tags=["extras_kaas"],
)

app_configs = app_config.AppConfig.get_all_configs()
limiter_str = app_configs["extras_kaas_limit"] + "/minute"


@router.get(
    "/render_url",
    summary="extras_kaas API to generate render link",
    response_model=RenderLinkResponse,
    responses=response_examples_extras,
)
@limiter.limit(limiter_str)
async def render_url(
    request: Request,
    documentID: Annotated[
        str,
        Query(
            max_length=64,
            pattern="^[ish_|pdf_]",
            description="ID of the document for which the render link URL needs to be created",
        ),
    ],
    token_payload: CoreTenant = Depends(JWTBearerTenantApiSwaggerAuthenticated()),
) -> RenderLinkResponse:
    """
    Generates render link URL for the given document ID

    Parameters:
    `documentID`: (str) ID of the document for which the render link URL needs to be created.
                  Accepts only the strings starting with 'ish_'

    Returns:
    A list of documentID and render link URL
    """

    result = None
    if documentID.startswith("ish_"):
        result = await RenderLinkService(None).renderlink_ish(documentID)
    if documentID.startswith("pdf_"):
        result = await RenderLinkService(None).renderlink_pdf(documentID)

    return result
