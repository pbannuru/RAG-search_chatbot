import json
from uuid import UUID
from sqlalchemy.orm import Session
from app.services.core_tenant_service import ServiceBase
from app.sql_app.dbenums.audit_log_enums import ContextEnum, ServiceEnum
from app.sql_app.dbmodels import core_audit_log


class CoreAuditLogService(ServiceBase):
    def __init__(self, db: Session):
        super().__init__(db)
        self.__model = core_audit_log.CoreAuditLog

    def get_logs(self):
        return self.db.query(self.__model).all()

    async def log_service_api(
        self,
        route: str,
        context: ContextEnum,
        service: ServiceEnum,
        tenant_id: UUID,
        log_input: dict[dict] = {},
        log_level: core_audit_log.LogLevelEnum = core_audit_log.LogLevelEnum.INFO,
        duration_ms: int = 0,
    ):
        log = self.__model(
            route=route,
            context=context,
            service=service,
            tenant_id=tenant_id,
            log_input=json.dumps(log_input),
            log_level=log_level,
            duration_ms=duration_ms,
        )
        self.db.add(log)
        self.db.commit()
        self.db.refresh(log)
        return log

    async def log_service_api_error(
        self,
        route: str,
        context: ContextEnum,
        service: ServiceEnum,
        tenant_id: UUID,
        stack_trace: str,
        log_input: dict = {},
        log_level: core_audit_log.LogLevelEnum = core_audit_log.LogLevelEnum.ERROR,
        duration_ms: int = 0,
    ):
        log = self.__model(
            route=route,
            context=context,
            service=service,
            tenant_id=tenant_id,
            log_input=json.dumps(log_input),
            log_level=log_level,
            duration_ms=duration_ms,
            stack_trace=stack_trace,
        )
        self.db.add(log)
        self.db.commit()
        self.db.refresh(log)
        return log
