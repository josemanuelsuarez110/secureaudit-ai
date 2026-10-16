"""Schemas Pydantic para ScanJob y ScanResult."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


# =========================================================
# ScanJob
# =========================================================

class ScanJobCreate(BaseModel):
    """Schema para crear un scan job."""

    asset_id: UUID
    scan_type: str = Field(
        default="full",
        pattern=r"^(full|tls|http|dns)$",
        description="Tipo de auditoría",
    )


class ScanJobResponse(BaseModel):
    """Schema de respuesta de ScanJob."""

    id: UUID
    organization_id: UUID
    asset_id: UUID
    created_by: UUID | None
    status: str
    scan_type: str
    priority: int
    started_at: datetime | None
    completed_at: datetime | None
    error_message: str | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


# =========================================================
# ScanResult
# =========================================================

class ScanResultResponse(BaseModel):
    """Schema de respuesta de ScanResult."""

    id: UUID
    scan_job_id: UUID
    asset_id: UUID
    category: str
    check_name: str
    status: str
    severity: str
    title: str
    description: str | None
    evidence: dict | None
    recommendation: str | None
    created_at: datetime

    model_config = {"from_attributes": True}


# =========================================================
# ScanJob con resultados (detalle)
# =========================================================

class ScanJobDetailResponse(ScanJobResponse):
    """Schema de ScanJob con sus resultados."""

    results: list[ScanResultResponse] = []
