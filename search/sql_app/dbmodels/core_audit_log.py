from dataclasses import dataclass
from datetime import datetime
from sqlalchemy import (
    UUID,
    Boolean,
    Column,
    DateTime,
    Enum,
    ForeignKey,
    Integer,
    String,
    text,
)
from app.sql_app.database import Base
import uuid as uuid_pkg
from sqlalchemy.orm import relationship

from app.sql_app.dbenums.audit_log_enums import ContextEnum, LogLevelEnum, ServiceEnum


class CoreAuditLog(Base):
    __tablename__ = "core_audit_logs"

    id: uuid_pkg.UUID = Column(
        String(36),
        server_default=text("(UUID())"),
        default=text("(UUID())"),
        primary_key=True,
        index=True,
    )

    tenant_id: uuid_pkg.UUID = Column(
        String(36), ForeignKey("core_tenants.uuid"), index=True
    )

    core_tenant = relationship("CoreTenant", back_populates="core_audit_log")

    timestamp: datetime = Column(
        DateTime(timezone=True),
        index=True,
        server_default=text("now()"),
        doc="The time the log entry was created, with Timezone information",
    )
    duration_ms: int = Column(Integer, default=0)

    route: str = Column(String(256))
    service: ServiceEnum = Column(Enum(ServiceEnum))
    # info or error
    log_level: LogLevelEnum = Column(Enum(LogLevelEnum), default=LogLevelEnum.INFO)

    context: ContextEnum = Column(
        Enum(ContextEnum),
    )

    # error message
    message: str = Column(String(512))

    # input given to the function/api that caused the error
    log_input: str = Column(String(1024))

    # stack trace
    stack_trace: str = Column(String(8192))
