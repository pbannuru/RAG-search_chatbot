from fastapi import Depends
from app.services.core_audit_log_service import CoreAuditLogService
from app.sql_app.database import DbDepends, get_db
from batch_jobs.internal.scheduler.task import Task

from sqlalchemy.orm import Session


class KaasTask(Task):
    def __init__(self):
        super().__init__("KaasTask")

    def run(self):
        super().run()
