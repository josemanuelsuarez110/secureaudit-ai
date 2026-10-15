"""Configuración de motores y sesiones de base de datos."""

from typing import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session

from app.core.config import settings


# Motor con RLS (usuario normal)
engine = create_engine(
    settings.DATABASE_URL,
    pool_pre_ping=True,
    echo=settings.APP_DEBUG,
)

# Motor con BYPASSRLS (usuario de sistema)
system_engine = create_engine(
    settings.SYSTEM_DATABASE_URL,
    pool_pre_ping=True,
    echo=settings.APP_DEBUG,
)


SessionLocal = sessionmaker(
    bind=engine,
    autocommit=False,
    autoflush=False,
    expire_on_commit=False,
)

SystemSessionLocal = sessionmaker(
    bind=system_engine,
    autocommit=False,
    autoflush=False,
    expire_on_commit=False,
)


def get_db() -> Generator[Session, None, None]:
    """Sesión normal (sujeta a RLS)."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_system_db() -> Generator[Session, None, None]:
    """Sesión de sistema (BYPASSRLS).

    USAR SOLO para:
    - Registro de usuarios (email check sin RLS)
    - Login (buscar usuario por email)
    - Tareas administrativas
    """
    db = SystemSessionLocal()
    try:
        yield db
    finally:
        db.close()
