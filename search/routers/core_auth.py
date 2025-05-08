from enum import Enum
from fastapi import APIRouter, Depends, Response
from sqlalchemy.orm import Session

from app.config.env import environment
from app.services.core_audit_log_service import CoreAuditLogService
from app.sql_app.database import get_db
import requests

router = APIRouter(
    prefix="/auth",
    tags=["auth"],
)
