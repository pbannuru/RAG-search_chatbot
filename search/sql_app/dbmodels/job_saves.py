from dataclasses import dataclass
from enum import Enum as EnumEnum
from sqlalchemy import (
    UUID,
    Boolean,
    Column,
    DateTime,
    Enum,
    Integer,
    String,
    UniqueConstraint,
)
from app.sql_app.database import Base


class JobSaves(Base):
    __tablename__ = "job_saves"

    job_key: str = Column(String(256), primary_key=True, index=True)
    last_run = Column(DateTime)
    last_successful_run = Column(DateTime)
