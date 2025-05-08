from pydantic import BaseModel, EmailStr


class CreateOpenSearchQueryDto(BaseModel):
    name: str
    opensearch_query: str = ""


class UpdateOpenSearchQueryDto(BaseModel):
    opensearch_query: str


class UpdateOpenSearchNameDto(BaseModel):
    name: str
