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


class EmailSettingsEventType(EnumEnum):
    SERVER_ERROR = "SERVER_ERROR"  # internal server error
    DOCUMENT_ERROR = "DOCUMENT_ERROR"


class EmailSettingsCategory(EnumEnum):
    APPLICATION = "APPLICATION"  # ALL OTHER
    KAAS = "KAAS"
    DOCHEBO = "DOCHEBO"


class EmailSubscriber(Base):
    __tablename__ = "job_email_subscribers"

    id: int = Column(Integer, primary_key=True, index=True, autoincrement=True)

    email = Column(String(256), index=True)

    # type of message the email is subscribed to
    event_type = Column(Enum(EmailSettingsEventType))

    # error on BU
    category = Column(Enum(EmailSettingsCategory))

    # is the email active
    is_active = Column(Boolean, default=True)

    # is the email a test email
    is_test = Column(Boolean, default=False)

    __table_args__ = (
        UniqueConstraint(
            "email", "event_type", "category", name="_email_event_category_uc"
        ),
    )
