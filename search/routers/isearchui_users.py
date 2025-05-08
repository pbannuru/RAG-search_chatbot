from fastapi import APIRouter, Depends, Request

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


router = APIRouter(
    prefix="/isearchui_user",
    tags=["isearchui_user"],
)


@router.post("/")
async def create_users(
    user: CreateUserDto,
    dependencies=Depends(JWTBearerTenantApiSwaggerAuthenticated()),
    db: Session = Depends(get_db),
):
    return ISearchUIUsersService(db).create_user(user)


@router.get("/")
async def get_users(
    db: Session = Depends(get_db),
    dependencies=Depends(JWTBearerTenantApiSwaggerAuthenticated()),
):
    return ISearchUIUsersService(db).get_users()


@router.get(
    "/auth/getUserFromToken",
)
async def getUserFromToken(
    request: Request,
    dependencies=Depends(JWTBearerISearchUserSwaggerAuthenticated()),
    db: Session = Depends(get_db),
):
    return ISearchUIUsersService(db).get_user(request.user.email)


@router.get("/{email}")
async def get_user(
    email: str,
    db: Session = Depends(get_db),
    dependencies=Depends(JWTBearerTenantApiSwaggerAuthenticated()),
):
    return ISearchUIUsersService(db).get_user_for_ui(email)
