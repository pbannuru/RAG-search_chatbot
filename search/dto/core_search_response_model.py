from datetime import datetime
from typing import Annotated, Optional
from pydantic import BaseModel, StringConstraints
from app.sql_app.dbenums.core_enums import (
    DomainEnum,
    PersonaEnum,
    SourceEnum,
    LanguageEnum,
)


class SearchResponseMetadata(BaseModel):
    limit: int
    size: int
    query: str
    device: Optional[str] = None
    persona: PersonaEnum
    domain: DomainEnum
    source: list[SourceEnum]
    language: LanguageEnum


class SearchResponseData(BaseModel):
    documentID: str
    score: float
    title: str
    description: str
    contentType: str
    contentUpdateDate: datetime
    score: Optional[float] = None
    parentDoc: Optional[str] = None
    language: LanguageEnum
    renderLink: Optional[Annotated[str, StringConstraints(min_length=10)]] = None
    products: list[str] = []
    relevant_text: Optional[str] = None


class SearchResponse(BaseModel):
    metadata: SearchResponseMetadata
    data: list[SearchResponseData]
