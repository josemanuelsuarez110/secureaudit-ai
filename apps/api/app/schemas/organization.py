"""Schemas Pydantic para Organization."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


class OrganizationBase(BaseModel):
    """Campos comunes de Organization."""

    name: str = Field(min_length=1, max_length=200)
    slug: str = Field(min_length=1, max_length=100, pattern=r"^[a-z0-9-]+$")


class OrganizationCreate(OrganizationBase):
    """Schema para crear organización."""

    pass


class OrganizationUpdate(BaseModel):
    """Schema para actualizar organización."""

    name: str | None = Field(default=None, min_length=1, max_length=200)


class OrganizationResponse(OrganizationBase):
    """Schema de respuesta de Organization."""

    id: UUID
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
