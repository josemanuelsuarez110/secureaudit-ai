"""Endpoints de organizaciones (CRUD)."""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import CurrentUser, DbDep
from app.db.session import get_system_db
from app.schemas import (
    OrganizationCreate,
    OrganizationResponse,
    OrganizationUpdate,
)
from app.services import (
    OrganizationError,
    create_organization,
    delete_organization,
    get_organization,
    list_user_organizations,
    update_organization,
)


router = APIRouter(prefix="/organizations", tags=["organizations"])

# Sesión de sistema para operaciones que necesitan BYPASSRLS (INSERT de org)
SystemDb = Annotated[Session, Depends(get_system_db)]


@router.get(
    "",
    response_model=list[OrganizationResponse],
    summary="Listar organizaciones del usuario",
)
def list_organizations(
    db: DbDep,
    current_user: CurrentUser,
) -> list[OrganizationResponse]:
    """Lista las organizaciones a las que pertenece el usuario."""
    orgs = list_user_organizations(db, current_user)
    return [OrganizationResponse.model_validate(o) for o in orgs]


@router.post(
    "",
    response_model=OrganizationResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Crear organización",
)
def create_org(
    payload: OrganizationCreate,
    db: SystemDb,                      # ← SystemDb (BYPASSRLS)
    current_user: CurrentUser,
) -> OrganizationResponse:
    """Crea una nueva organización y asigna al usuario como admin."""
    try:
        org = create_organization(
            db,
            user=current_user,
            name=payload.name,
            slug=payload.slug,
        )
    except OrganizationError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc

    return OrganizationResponse.model_validate(org)


@router.get(
    "/{organization_id}",
    response_model=OrganizationResponse,
    summary="Ver organización",
)
def get_org(
    organization_id: UUID,
    db: DbDep,
    current_user: CurrentUser,
) -> OrganizationResponse:
    """Retorna el detalle de una organización."""
    try:
        org = get_organization(db, current_user, organization_id)
    except OrganizationError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc

    return OrganizationResponse.model_validate(org)


@router.patch(
    "/{organization_id}",
    response_model=OrganizationResponse,
    summary="Actualizar organización",
)
def update_org(
    organization_id: UUID,
    payload: OrganizationUpdate,
    db: DbDep,
    current_user: CurrentUser,
) -> OrganizationResponse:
    """Actualiza una organización. Solo admin."""
    try:
        org = update_organization(
            db,
            user=current_user,
            organization_id=organization_id,
            name=payload.name,
        )
    except OrganizationError as exc:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(exc),
        ) from exc

    return OrganizationResponse.model_validate(org)


@router.delete(
    "/{organization_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Eliminar organización",
)
def delete_org(
    organization_id: UUID,
    db: DbDep,
    current_user: CurrentUser,
) -> None:
    """Elimina una organización. Solo admin."""
    try:
        delete_organization(db, user=current_user, organization_id=organization_id)
    except OrganizationError as exc:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(exc),
        ) from exc
