"""Servicio de scans (auditorías)."""

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.rls import set_rls_context
from app.models import Asset, Membership, ScanJob, ScanResult, User


class ScanError(Exception):
    """Error de scans."""

    pass


def _get_membership(
    db: Session, user: User, organization_id: UUID
) -> Membership:
    """Verifica que el usuario sea miembro de la organización."""
    set_rls_context(db, user.id)
    membership = db.execute(
        select(Membership).where(
            Membership.user_id == user.id,
            Membership.organization_id == organization_id,
        )
    ).scalar_one_or_none()

    if not membership:
        raise ScanError("No eres miembro de esta organización")
    return membership


def list_scan_jobs(
    db: Session, user: User, organization_id: UUID
) -> list[ScanJob]:
    """Lista los scan jobs de una organización."""
    _get_membership(db, user, organization_id)
    set_rls_context(db, user.id)

    return list(
        db.execute(
            select(ScanJob)
            .where(ScanJob.organization_id == organization_id)
            .order_by(ScanJob.created_at.desc())
        ).scalars().all()
    )


def get_scan_job(db: Session, user: User, scan_job_id: UUID) -> ScanJob:
    """Obtiene un scan job por ID. Verifica membership."""
    set_rls_context(db, user.id)
    job = db.execute(
        select(ScanJob).where(ScanJob.id == scan_job_id)
    ).scalar_one_or_none()

    if not job:
        raise ScanError("Scan job no encontrado o sin acceso")
    return job


def get_scan_results(
    db: Session, user: User, scan_job_id: UUID
) -> list[ScanResult]:
    """Obtiene los resultados de un scan job."""
    get_scan_job(db, user, scan_job_id)  # verifica membership
    set_rls_context(db, user.id)

    return list(
        db.execute(
            select(ScanResult)
            .where(ScanResult.scan_job_id == scan_job_id)
            .order_by(ScanResult.created_at)
        ).scalars().all()
    )


def create_scan_job(
    db: Session,
    user: User,
    organization_id: UUID,
    asset_id: UUID,
    scan_type: str = "full",
) -> ScanJob:
    """Crea un scan job en la cola."""
    _get_membership(db, user, organization_id)
    set_rls_context(db, user.id)

    # Verificar que el asset exista y pertenezca a la organización
    asset = db.execute(
        select(Asset).where(
            Asset.id == asset_id,
            Asset.organization_id == organization_id,
        )
    ).scalar_one_or_none()

    if not asset:
        raise ScanError("Asset no encontrado en esta organización")

    # Verificar que el asset esté verificado
    if asset.status != "active":
        raise ScanError(
            "El asset debe estar verificado (status='active') antes de auditarlo"
        )

    # Verificar que no haya un job pendiente/en curso para el mismo asset
    existing = db.execute(
        select(ScanJob).where(
            ScanJob.asset_id == asset_id,
            ScanJob.status.in_(["pending", "running"]),
        )
    ).scalar_one_or_none()

    if existing:
        raise ScanError("Ya hay una auditoría en curso para este asset")

    job = ScanJob(
        organization_id=organization_id,
        asset_id=asset_id,
        created_by=user.id,
        status="pending",
        scan_type=scan_type,
        priority=5,
    )
    db.add(job)
    db.commit()

    set_rls_context(db, user.id)
    job = db.execute(
        select(ScanJob).where(ScanJob.id == job.id)
    ).scalar_one()

    return job


def cancel_scan_job(
    db: Session, user: User, scan_job_id: UUID
) -> ScanJob:
    """Cancela un scan job (si aún no ha empezado o está en curso)."""
    job = get_scan_job(db, user, scan_job_id)

    if job.status not in ("pending", "running"):
        raise ScanError(
            f"No se puede cancelar un job con estado '{job.status}'"
        )

    job.status = "cancelled"
    db.commit()

    set_rls_context(db, user.id)
    job = db.execute(
        select(ScanJob).where(ScanJob.id == scan_job_id)
    ).scalar_one()

    return job
