from dataclasses import dataclass
from datetime import datetime
from enum import Enum as EnumEnum
import uuid
from sqlalchemy import (
    UUID,
    VARCHAR,
    Boolean,
    Column,
    DateTime,
    Enum,
    Integer,
    String,
    UniqueConstraint,
    text,
)
from app.sql_app.database import Base


class RoleEnum(EnumEnum):
    Admin = "admin"
    Guest = "guest"


class ISearchUIUser(Base):
    __tablename__ = "isearchui_users"

    email: str = Column(String(512), primary_key=True, nullable=False)

    # Search Inputs
    role: RoleEnum = Column(Enum(RoleEnum), nullable=False, default=RoleEnum.Guest)

    created_by: str = Column(String(512), primary_key=False, nullable=True)
    created_at: datetime = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=text("now()"),
    )

    is_authenticated: bool = True
