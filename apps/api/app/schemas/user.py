"""Schemas Pydantic para User."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field


class UserBase(BaseModel):
    """Campos comunes de User."""

    email: EmailStr
    full_name: str | None = None


class UserCreate(UserBase):
    """Schema para registro de usuario."""

    password: str = Field(min_length=8, max_length=128)


class UserLogin(BaseModel):
    """Schema para login."""

    email: EmailStr
    password: str


class UserResponse(UserBase):
    """Schema de respuesta de User (sin password)."""

    id: UUID
    is_active: bool
    is_superuser: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class Token(BaseModel):
    """Schema de respuesta de autenticación."""

    access_token: str
    token_type: str = "bearer"


class TokenPayload(BaseModel):
    """Payload decodificado del JWT."""

    sub: str
    exp: int
    type: str
