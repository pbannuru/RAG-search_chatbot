from datetime import datetime
import uuid as uuid_pkg
from sqlalchemy import Boolean, Column, DateTime, String
from sqlalchemy.sql.expression import text
from app.sql_app.database import Base
from sqlalchemy.orm import relationship


class CoreTenant(Base):
    __tablename__ = "core_tenants"

    uuid: uuid_pkg.UUID = Column(
        String(36),
        server_default=text("(UUID())"),
        default=text("(UUID())"),
        primary_key=True,
        index=True,
    )
    client_id: str = Column(String(32), index=True, unique=True)

    created_at: datetime = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=text("now()"),
    )
    created_by: str = Column(String(256), nullable=False)

    updated_at: datetime = Column(
        DateTime(timezone=True),
        nullable=True,
        server_onupdate=text("now()"),
    )
    last_updated_by: str = Column(String(256), nullable=True)

    deleted_at: datetime = Column(
        DateTime(timezone=True),
        nullable=True,
    )

    core_audit_log = relationship("CoreAuditLog", back_populates="core_tenant")

    application_admin: bool = Column(
        Boolean, default=False, nullable=False, server_default=text("0")
    )

    # used by exception handler
    is_authenticated: bool = True
