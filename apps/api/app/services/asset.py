"""Servicio de assets (dominios)."""

import secrets
from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.rls import set_rls_context
from app.models import Asset, Membership, User
from app.services.dns import verify_txt_record


class AssetError(Exception):
    """Error de assets."""

    pass


def _generate_verification_token() -> str:
    """Genera un token único para verificación DNS TXT."""
    return secrets.token_urlsafe(32)


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
        raise AssetError("No eres miembro de esta organización")
    return membership


def list_organization_assets(
    db: Session, user: User, organization_id: UUID
) -> list[Asset]:
    """Lista los assets de una organización."""
    _get_membership(db, user, organization_id)
    set_rls_context(db, user.id)

    return list(
        db.execute(
            select(Asset)
            .where(Asset.organization_id == organization_id)
            .order_by(Asset.created_at.desc())
        ).scalars().all()
    )


def get_asset(db: Session, user: User, asset_id: UUID) -> Asset:
    """Obtiene un asset por ID. Verifica membership."""
    set_rls_context(db, user.id)
    asset = db.execute(
        select(Asset).where(Asset.id == asset_id)
    ).scalar_one_or_none()

    if not asset:
        raise AssetError("Asset no encontrado o sin acceso")
    return asset


def create_asset(
    db: Session,
    user: User,
    organization_id: UUID,
    domain: str,
    display_name: str | None = None,
) -> Asset:
    """Crea un nuevo asset en una organización."""
    _get_membership(db, user, organization_id)
    set_rls_context(db, user.id)

    existing = db.execute(
        select(Asset).where(
            Asset.organization_id == organization_id,
            Asset.domain == domain,
        )
    ).scalar_one_or_none()

    if existing:
        raise AssetError("Este dominio ya está registrado en la organización")

    asset = Asset(
        organization_id=organization_id,
        domain=domain,
        display_name=display_name,
        status="pending_verification",
        verification_token=_generate_verification_token(),
    )
    db.add(asset)
    db.commit()

    set_rls_context(db, user.id)
    asset = db.execute(
        select(Asset).where(Asset.id == asset.id)
    ).scalar_one()

    return asset


def update_asset(
    db: Session,
    user: User,
    asset_id: UUID,
    display_name: str | None = None,
    status: str | None = None,
) -> Asset:
    """Actualiza un asset."""
    asset = get_asset(db, user, asset_id)

    if display_name is not None:
        asset.display_name = display_name
    if status is not None:
        asset.status = status

    db.commit()

    set_rls_context(db, user.id)
    asset = db.execute(
        select(Asset).where(Asset.id == asset_id)
    ).scalar_one()

    return asset


def delete_asset(db: Session, user: User, asset_id: UUID) -> None:
    """Elimina un asset."""
    asset = get_asset(db, user, asset_id)
    db.delete(asset)
    db.commit()


def verify_asset(db: Session, user: User, asset_id: UUID) -> dict:
    """Verifica el asset vía DNS TXT."""
    asset = get_asset(db, user, asset_id)

    record_name = f"_secureaudit.{asset.domain}"
    record_value = f"secureaudit-verification={asset.verification_token}"

    verified, message = verify_txt_record(
        domain=asset.domain,
        expected_value=record_value,
        record_name=record_name,
    )

    if not verified:
        return {
            "verified": False,
            "message": message,
            "domain": asset.domain,
            "verification_token": asset.verification_token,
            "record_name": record_name,
            "record_type": "TXT",
            "record_value": record_value,
        }

    asset.status = "active"
    asset.verified_at = datetime.now(timezone.utc)
    db.commit()

    set_rls_context(db, user.id)
    asset = db.execute(
        select(Asset).where(Asset.id == asset_id)
    ).scalar_one()

    return {
        "verified": True,
        "message": "Asset verificado correctamente",
        "domain": asset.domain,
        "verification_token": asset.verification_token,
        "record_name": record_name,
        "record_type": "TXT",
        "record_value": record_value,
    }
