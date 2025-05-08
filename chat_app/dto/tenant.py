from fastapi import Body
from pydantic import BaseModel, EmailStr
from typing import Annotated


class CreateTenantIn(BaseModel):
    client_id: Annotated[str, Body(min_length=32, max_length=32)]
    created_by: EmailStr
