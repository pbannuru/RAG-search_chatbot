from typing import List, Optional
from pydantic import BaseModel, validator, HttpUrl
from app.sql_app.dbenums.core_enums import LanguageEnum
import re


class BulkRenderLinkMetadata(BaseModel):
    language: LanguageEnum
    documentID: List[str]

    @validator(
        "documentID", each_item=True
    )  # Using validator helps in applying the constraints to each item in list query parameter `documentIDs`
    def check_pattern(cls, docID):
        pattern = r"^(ish_|pdf_)"
        if not re.match(pattern, docID):
            raise ValueError("Each document ID must start with either `ish_` or `pdf_`")
        return docID


class RenderLink(BaseModel):
    documentid: str
    success: bool
    render_link: Optional[HttpUrl] = None
    error_message: Optional[str] = None
    language: Optional[str] = None


class BulkRenderLinkResponse(BaseModel):
    metadata: BulkRenderLinkMetadata
    data: List[RenderLink]
