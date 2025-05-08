from fastapi import APIRouter, Depends

from app.dto.tenant import CreateTenantIn
from app.middlewares.authentication import VerifiedTokenBody
from app.services.core_auth import (
    JWTBearerApplicationAdminOnly,
)
from app.services.core_tenant_service import CoreTenantService
from app.sql_app.database import get_db
from sqlalchemy.orm import Session

router = APIRouter(
    prefix="/core_tenant",
    tags=["core_tenant"],
)


@router.get("/from_token")
async def get_from_token(
    db: Session = Depends(get_db),
    token_payload: VerifiedTokenBody = Depends(JWTBearerApplicationAdminOnly()),
):
    return CoreTenantService(db).get_by_client_id(token_payload.client_id)


@router.get(
    "/{tenant_id}",
    dependencies=[Depends(JWTBearerApplicationAdminOnly())],
)
async def get_one(tenant_id: str | None, db: Session = Depends(get_db)):
    return CoreTenantService(db).get_one(tenant_id)


@router.get(
    "/",
    dependencies=[Depends(JWTBearerApplicationAdminOnly())],
)
async def get_all(db: Session = Depends(get_db)):
    return CoreTenantService(db).get_all()


@router.post(
    "/",
    dependencies=[Depends(JWTBearerApplicationAdminOnly())],
)
async def create(create_tenant_dto: CreateTenantIn, db: Session = Depends(get_db)):
    return CoreTenantService(db).create(create_tenant_dto)
