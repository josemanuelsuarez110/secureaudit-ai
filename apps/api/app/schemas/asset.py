"""Schemas Pydantic para Asset."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


DOMAIN_PATTERN = r"^[a-z0-9]([a-z0-9-]*[a-z0-9])?(\.[a-z0-9]([a-z0-9-]*[a-z0-9])?)+$"


class AssetBase(BaseModel):
    """Campos comunes de Asset."""

    domain: str = Field(
        min_length=3,
        max_length=255,
        pattern=DOMAIN_PATTERN,
        description="Dominio (ej. ejemplo.com)",
    )
    display_name: str | None = Field(
        default=None,
        max_length=255,
        description="Nombre descriptivo (ej. Sitio principal)",
    )


class AssetCreate(AssetBase):
    """Schema para crear asset."""

    pass


class AssetUpdate(BaseModel):
    """Schema para actualizar asset."""

    display_name: str | None = Field(default=None, max_length=255)
    status: str | None = Field(default=None, pattern=r"^(active|paused|archived)$")


class AssetResponse(AssetBase):
    """Schema de respuesta de Asset."""

    id: UUID
    organization_id: UUID
    status: str
    verification_token: str
    verified_at: datetime | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class AssetVerificationResponse(BaseModel):
    """Respuesta de verificación DNS."""

    verified: bool
    message: str
    domain: str
    verification_token: str
    record_name: str  # ej. _secureaudit.ejemplo.com
    record_type: str  # "TXT"
    record_value: str  # ej. "secureaudit-verification=<token>"
