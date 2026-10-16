"""Endpoints de scans (auditorías)."""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import CurrentUser, DbDep
from app.db.session import get_system_db
from app.schemas import (
    ScanJobCreate,
    ScanJobDetailResponse,
    ScanJobResponse,
    ScanResultResponse,
)
from app.services import (
    ScanError,
    cancel_scan_job,
    create_scan_job,
    get_scan_job,
    get_scan_results,
    list_scan_jobs,
)


router = APIRouter(prefix="/scans", tags=["scans"])

# SystemDb para crear jobs (BYPASSRLS)
SystemDb = Annotated[Session, Depends(get_system_db)]


# =========================================================
# Endpoints anidados en organizaciones
# =========================================================

@router.get(
    "/organizations/{organization_id}/scans",
    response_model=list[ScanJobResponse],
    summary="Listar scan jobs de una organización",
)
def list_jobs(
    organization_id: UUID,
    db: DbDep,
    current_user: CurrentUser,
) -> list[ScanJobResponse]:
    """Lista los scan jobs de una organización."""
    try:
        jobs = list_scan_jobs(db, current_user, organization_id)
    except ScanError as exc:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(exc),
        ) from exc

    return [ScanJobResponse.model_validate(j) for j in jobs]


@router.post(
    "/organizations/{organization_id}/scans",
    response_model=ScanJobResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Crear scan job",
)
def create_job(
    organization_id: UUID,
    payload: ScanJobCreate,
    db: SystemDb,                     # SystemDb (BYPASSRLS) para el INSERT
    current_user: CurrentUser,
) -> ScanJobResponse:
    """Crea un scan job en la cola."""
    try:
        job = create_scan_job(
            db,
            user=current_user,
            organization_id=organization_id,
            asset_id=payload.asset_id,
            scan_type=payload.scan_type,
        )
    except ScanError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc

    return ScanJobResponse.model_validate(job)


# =========================================================
# Endpoints directos por ID de job
# =========================================================

@router.get(
    "/{scan_job_id}",
    response_model=ScanJobDetailResponse,
    summary="Ver scan job con resultados",
)
def get_job(
    scan_job_id: UUID,
    db: DbDep,
    current_user: CurrentUser,
) -> ScanJobDetailResponse:
    """Retorna el detalle de un scan job con sus resultados."""
    try:
        job = get_scan_job(db, current_user, scan_job_id)
        results = get_scan_results(db, current_user, scan_job_id)
    except ScanError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc

    return ScanJobDetailResponse(
        **ScanJobResponse.model_validate(job).model_dump(),
        results=[ScanResultResponse.model_validate(r) for r in results],
    )


@router.get(
    "/{scan_job_id}/results",
    response_model=list[ScanResultResponse],
    summary="Ver resultados de un scan job",
)
def get_job_results(
    scan_job_id: UUID,
    db: DbDep,
    current_user: CurrentUser,
) -> list[ScanResultResponse]:
    """Retorna los resultados de un scan job."""
    try:
        results = get_scan_results(db, current_user, scan_job_id)
    except ScanError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc

    return [ScanResultResponse.model_validate(r) for r in results]


@router.post(
    "/{scan_job_id}/cancel",
    response_model=ScanJobResponse,
    summary="Cancelar scan job",
)
def cancel_job(
    scan_job_id: UUID,
    db: DbDep,
    current_user: CurrentUser,
) -> ScanJobResponse:
    """Cancela un scan job pendiente o en curso."""
    try:
        job = cancel_scan_job(db, current_user, scan_job_id)
    except ScanError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc

    return ScanJobResponse.model_validate(job)
