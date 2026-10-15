"""Endpoints de autenticación: registro, login y perfil."""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import CurrentUser, get_db
from app.db.session import get_system_db
from app.schemas import (
    OrganizationResponse,
    Token,
    UserCreate,
    UserLogin,
    UserResponse,
)
from app.services import (
    AuthError,
    authenticate_user,
    create_user_token,
    register_user,
)


router = APIRouter(prefix="/auth", tags=["auth"])

SystemDb = Annotated[Session, Depends(get_system_db)]
NormalDb = Annotated[Session, Depends(get_db)]


@router.post(
    "/register",
    response_model=dict,
    status_code=status.HTTP_201_CREATED,
    summary="Registrar un nuevo usuario",
)
def register(payload: UserCreate, db: SystemDb) -> dict:
    """Registra un nuevo usuario (usa rol de sistema para email check)."""
    try:
        user, organization = register_user(
            db,
            email=payload.email,
            password=payload.password,
            full_name=payload.full_name,
        )
    except AuthError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc

    token = create_user_token(user)

    return {
        "user": UserResponse.model_validate(user),
        "organization": (
            OrganizationResponse.model_validate(organization)
            if organization
            else None
        ),
        "access_token": token,
        "token_type": "bearer",
    }


@router.post(
    "/login",
    response_model=Token,
    summary="Iniciar sesión",
)
def login(payload: UserLogin, db: SystemDb) -> Token:
    """Autentica un usuario (usa rol de sistema para buscar por email)."""
    try:
        user = authenticate_user(db, email=payload.email, password=payload.password)
    except AuthError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(exc),
            headers={"WWW-Authenticate": "Bearer"},
        ) from exc

    token = create_user_token(user)
    return Token(access_token=token, token_type="bearer")


@router.get(
    "/me",
    response_model=UserResponse,
    summary="Obtener usuario actual",
)
def me(current_user: CurrentUser) -> UserResponse:
    """Retorna el usuario autenticado (usa RLS normal)."""
    return UserResponse.model_validate(current_user)
