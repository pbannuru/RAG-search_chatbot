from sqlalchemy import (
    Column,
    Integer,
    String,
    Text,
)
from app.sql_app.database import Base


class ISearchUIOpenSearchQueries(Base):
    __tablename__ = "isearchui_opensearch_queries"

    id: int = Column(Integer, primary_key=True, index=True, autoincrement=True)
    name: str = Column(String(512), unique=True)
    opensearch_query = Column(Text())
