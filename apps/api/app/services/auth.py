"""Servicio de autenticación: registro, login y creación de organizaciones."""

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.rls import set_rls_context
from app.core.security import create_access_token, hash_password, verify_password
from app.models import Membership, Organization, User


class AuthError(Exception):
    """Error de autenticación."""

    pass


def register_user(
    db: Session,
    email: str,
    password: str,
    full_name: str | None = None,
    organization_name: str | None = None,
    organization_slug: str | None = None,
) -> tuple[User, Organization | None]:
    """Registra un nuevo usuario y, opcionalmente, crea una organización.

    Retorna (user, organization). La organización es None si no se especifica.
    """
    # Verificar que el email no exista
    existing = db.execute(select(User).where(User.email == email)).scalar_one_or_none()
    if existing:
        raise AuthError("El email ya está registrado")

    # Crear usuario
    user = User(
        email=email,
        hashed_password=hash_password(password),
        full_name=full_name,
        is_active=True,
        is_superuser=False,
    )
    db.add(user)
    db.flush()  # para tener el ID

    organization = None

    # Si se especifica organización, crearla + membership
    if organization_name and organization_slug:
        # Verificar slug único
        existing_org = db.execute(
            select(Organization).where(Organization.slug == organization_slug)
        ).scalar_one_or_none()
        if existing_org:
            raise AuthError("El slug de organización ya está en uso")

        organization = Organization(
            name=organization_name,
            slug=organization_slug,
        )
        db.add(organization)
        db.flush()

        # Crear membership como admin
        membership = Membership(
            user_id=user.id,
            organization_id=organization.id,
            role="admin",
        )
        db.add(membership)
        db.flush()

    db.commit()
    db.refresh(user)
    if organization:
        db.refresh(organization)

    return user, organization


def authenticate_user(db: Session, email: str, password: str) -> User:
    """Autentica un usuario. Lanza AuthError si falla."""
    user = db.execute(select(User).where(User.email == email)).scalar_one_or_none()

    # Mensaje genérico (no revelar si el email existe)
    if not user:
        raise AuthError("Credenciales inválidas")
    if not user.is_active:
        raise AuthError("Cuenta desactivada")
    if not verify_password(password, user.hashed_password):
        raise AuthError("Credenciales inválidas")

    return user


def create_user_token(user: User) -> str:
    """Genera un JWT de acceso para un usuario."""
    return create_access_token(subject=str(user.id))
