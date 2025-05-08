from pydantic import BaseModel, EmailStr


class CreateUserDto(BaseModel):
    email: str
    created_by: EmailStr = "system@auto.hp"
