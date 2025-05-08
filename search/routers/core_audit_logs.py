from enum import Enum
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.config.env import environment
from app.services.core_audit_log_service import CoreAuditLogService
from app.sql_app.database import get_db

router = APIRouter(
    prefix="/audit-logs",
    tags=["audit-logs"],
)


# @router.get("")
# async def audit(db: Session = Depends(get_db)):
#     return CoreAuditLogService(db).get_logs()
