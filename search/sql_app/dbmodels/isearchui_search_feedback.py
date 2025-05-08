from sqlalchemy import (
    Column,
    DateTime,
    Enum,
    Integer,
    String,
)
from app.sql_app.database import Base
from app.sql_app.dbenums.core_enums import PersonaEnum
from app.sql_app.dbenums.feedbacks_enums import ImpressionEnum


class ISearchUISearchFeedback(Base):
    __tablename__ = "isearchui_search_feedbacks"

    id: str = Column(Integer, primary_key=True, index=True)

    impression: ImpressionEnum = Column(Enum(ImpressionEnum), nullable=False)

    # Search Inputs
    search_text = Column(String(512))
    search_device = Column(String(256))
    search_persona: PersonaEnum = Column(Enum(PersonaEnum), nullable=False)

    # Feedback
    feedback_text = Column(String(512))
    feedback_timestamp = Column(DateTime)
    feedback_by = Column(String(256))

    # Search Results
    on_document_id = Column(String(512))
    on_document_title = Column(String(512))
    on_document_description = Column(String(512))

    on_result_position: int = Column(Integer)
