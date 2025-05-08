from datetime import datetime
from sqlalchemy import Boolean, Column, DateTime, String
from sqlalchemy.sql.expression import text
from sqlalchemy.orm import relationship
from app.sql_app.database import Base
from sqlalchemy import Column, DateTime, Integer, String, text, Text, Float


class RagasEvaluation(Base):
    __tablename__ = "ragas_evaluation"

    id = Column(Integer, primary_key=True, autoincrement=True)
    session_id = Column(Text, nullable=False)
    user_input: str = Column(Text, nullable=False)
    response: str = Column(Text, nullable=True)
    retrieved_contexts: str = Column(Text, nullable=True)  # JSON stringified list
    faithfulness_score: float = Column(Float, nullable=True)
    context_precision_score: float = Column(Float, nullable=True)
    factual_correctness_score: float = Column(Float, nullable=True)

    created_at: datetime = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=text("now()"),
    )

