"""Endpoints de assets (dominios)."""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import CurrentUser, DbDep
from app.db.session import get_system_db
from app.schemas import (
    AssetCreate,
    AssetResponse,
    AssetUpdate,
    AssetVerificationResponse,
)
from app.services import (
    AssetError,
    create_asset,
    delete_asset,
    get_asset,
    list_organization_assets,
    update_asset,
    verify_asset,
)


router = APIRouter(prefix="/assets", tags=["assets"])

# SystemDb para crear assets (BYPASSRLS)
SystemDb = Annotated[Session, Depends(get_system_db)]


# =========================================================
# Endpoints anidados en organizaciones
# =========================================================

@router.get(
    "/organizations/{organization_id}/assets",
    response_model=list[AssetResponse],
    summary="Listar assets de una organización",
)
def list_assets(
    organization_id: UUID,
    db: DbDep,
    current_user: CurrentUser,
) -> list[AssetResponse]:
    """Lista los assets de una organización (si eres miembro)."""
    try:
        assets = list_organization_assets(db, current_user, organization_id)
    except AssetError as exc:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(exc),
        ) from exc

    return [AssetResponse.model_validate(a) for a in assets]


@router.post(
    "/organizations/{organization_id}/assets",
    response_model=AssetResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Crear asset",
)
def create_new_asset(
    organization_id: UUID,
    payload: AssetCreate,
    db: SystemDb,                      # SystemDb (BYPASSRLS) para el INSERT
    current_user: CurrentUser,
) -> AssetResponse:
    """Crea un nuevo asset en una organización (si eres miembro)."""
    try:
        asset = create_asset(
            db,
            user=current_user,
            organization_id=organization_id,
            domain=payload.domain,
            display_name=payload.display_name,
        )
    except AssetError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc

    return AssetResponse.model_validate(asset)


# =========================================================
# Endpoints directos por ID de asset
# =========================================================

@router.get(
    "/{asset_id}",
    response_model=AssetResponse,
    summary="Ver asset",
)
def get_single_asset(
    asset_id: UUID,
    db: DbDep,
    current_user: CurrentUser,
) -> AssetResponse:
    """Retorna el detalle de un asset."""
    try:
        asset = get_asset(db, current_user, asset_id)
    except AssetError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc

    return AssetResponse.model_validate(asset)


@router.patch(
    "/{asset_id}",
    response_model=AssetResponse,
    summary="Actualizar asset",
)
def update_single_asset(
    asset_id: UUID,
    payload: AssetUpdate,
    db: DbDep,
    current_user: CurrentUser,
) -> AssetResponse:
    """Actualiza un asset."""
    try:
        asset = update_asset(
            db,
            user=current_user,
            asset_id=asset_id,
            display_name=payload.display_name,
            status=payload.status,
        )
    except AssetError as exc:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(exc),
        ) from exc

    return AssetResponse.model_validate(asset)


@router.delete(
    "/{asset_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Eliminar asset",
)
def delete_single_asset(
    asset_id: UUID,
    db: DbDep,
    current_user: CurrentUser,
) -> None:
    """Elimina un asset."""
    try:
        delete_asset(db, user=current_user, asset_id=asset_id)
    except AssetError as exc:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(exc),
        ) from exc


@router.post(
    "/{asset_id}/verify",
    response_model=AssetVerificationResponse,
    summary="Verificar asset vía DNS TXT",
)
def verify_single_asset(
    asset_id: UUID,
    db: DbDep,
    current_user: CurrentUser,
) -> AssetVerificationResponse:
    """Verifica un asset vía DNS TXT.

    Por ahora simula la verificación. TODO: DNS real.
    """
    try:
        result = verify_asset(db, user=current_user, asset_id=asset_id)
    except AssetError as exc:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(exc),
        ) from exc

    return AssetVerificationResponse(**result)
