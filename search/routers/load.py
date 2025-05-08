from typing import Annotated
from fastapi import APIRouter, Depends, Query, Request

# from app.config.env import environment
from app.dto.isearchui_users import CreateUserDto
from app.middlewares.authentication import (
    JWTBearerISearchUserSwaggerAuthenticated,
    JWTBearerTenantApiSwaggerAuthenticated,
    VerifiedTokenBody,
)
from app.services.isearchui_users_service import ISearchUIUsersService
from app.sql_app.database import get_db
from sqlalchemy.orm import Session


simple_router = APIRouter(
    prefix="/baseline",
    tags=["baseline"],
)


@simple_router.get("/")
async def get_simple():
    return True


@simple_router.post("/")
async def post_simple():
    return True


tenant_router = APIRouter(
    prefix="/baseline",
    tags=["baseline"],
)


@tenant_router.get("/")
async def get_tenant(
    token_payload=Depends(JWTBearerTenantApiSwaggerAuthenticated()),
    db: Session = Depends(get_db),
):
    return True


@tenant_router.post("/")
async def post_tenant(
    token_payload=Depends(JWTBearerTenantApiSwaggerAuthenticated()),
    db: Session = Depends(get_db),
):
    return True
