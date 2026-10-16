"""Servicio de organizaciones (CRUD)."""

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.rls import set_rls_context
from app.models import Membership, Organization, User


class OrganizationError(Exception):
    """Error de organizaciones."""

    pass


def list_user_organizations(db: Session, user: User) -> list[Organization]:
    """Lista las organizaciones a las que pertenece el usuario.

    RLS filtra automáticamente por membership.
    """
    set_rls_context(db, user.id)
    return list(db.execute(select(Organization)).scalars().all())


def get_organization(
    db: Session, user: User, organization_id: UUID
) -> Organization:
    """Obtiene una organización. Verifica que el usuario sea miembro."""
    set_rls_context(db, user.id)
    org = db.execute(
        select(Organization).where(Organization.id == organization_id)
    ).scalar_one_or_none()

    if not org:
        raise OrganizationError("Organización no encontrada o sin acceso")
    return org


def create_organization(
    db: Session,
    user: User,
    name: str,
    slug: str,
) -> Organization:
    """Crea una nueva organización y asigna al usuario como admin."""
    # Verificar slug único (usando contexto RLS del usuario,
    # pero el unique constraint lo garantiza a nivel DB)
    existing = db.execute(
        select(Organization).where(Organization.slug == slug)
    ).scalar_one_or_none()

    if existing:
        raise OrganizationError("El slug ya está en uso")

    org = Organization(name=name, slug=slug)
    db.add(org)
    db.flush()

    # Crear membership como admin
    membership = Membership(
        user_id=user.id,
        organization_id=org.id,
        role="admin",
    )
    db.add(membership)
    db.commit()

    # Después del commit, refrescar con contexto RLS para leer la org
    set_rls_context(db, user.id)
    org = db.execute(
        select(Organization).where(Organization.id == org.id)
    ).scalar_one()

    return org


def update_organization(
    db: Session,
    user: User,
    organization_id: UUID,
    name: str | None = None,
) -> Organization:
    """Actualiza una organización. Solo admin."""
    # Verificar que el usuario sea admin
    membership = _get_membership(db, user, organization_id)
    if membership.role != "admin":
        raise OrganizationError("Solo admin puede actualizar la organización")

    org = get_organization(db, user, organization_id)

    if name is not None:
        org.name = name

    db.commit()

    # Refrescar con contexto RLS
    set_rls_context(db, user.id)
    org = db.execute(
        select(Organization).where(Organization.id == organization_id)
    ).scalar_one()

    return org


def delete_organization(
    db: Session,
    user: User,
    organization_id: UUID,
) -> None:
    """Elimina una organización. Solo admin."""
    membership = _get_membership(db, user, organization_id)
    if membership.role != "admin":
        raise OrganizationError("Solo admin puede eliminar la organización")

    org = get_organization(db, user, organization_id)
    db.delete(org)
    db.commit()


def _get_membership(
    db: Session, user: User, organization_id: UUID
) -> Membership:
    """Obtiene el membership del usuario en una organización."""
    set_rls_context(db, user.id)
    membership = db.execute(
        select(Membership).where(
            Membership.user_id == user.id,
            Membership.organization_id == organization_id,
        )
    ).scalar_one_or_none()

    if not membership:
        raise OrganizationError("No eres miembro de esta organización")
    return membership
