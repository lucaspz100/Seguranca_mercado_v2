import uuid
from datetime import datetime

from pydantic import BaseModel, EmailStr, field_validator

from sinc.schemas.common import Role


class UserCreate(BaseModel):
    email: EmailStr
    username: str
    password: str
    role: Role = Role.OPERATOR

    @field_validator("username")
    @classmethod
    def username_min_length(cls, v: str) -> str:
        if len(v) < 3:
            raise ValueError("username deve ter ao menos 3 caracteres")
        return v

    @field_validator("password")
    @classmethod
    def password_min_length(cls, v: str) -> str:
        if len(v) < 8:
            raise ValueError("senha deve ter ao menos 8 caracteres")
        return v


class UserResponse(BaseModel):
    id: uuid.UUID
    email: str
    username: str
    role: Role
    is_active: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class UserListResponse(BaseModel):
    items: list[UserResponse]
    total: int
