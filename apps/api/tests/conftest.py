"""Fixtures de pytest para tests."""

import os
from typing import Generator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session

# Sobrescribir variables de entorno ANTES de importar la app
os.environ.setdefault("DATABASE_URL", "postgresql+psycopg://secureaudit:secureaudit_dev_pass@localhost:5432/secureaudit_test")
os.environ.setdefault("SYSTEM_DATABASE_URL", "postgresql+psycopg://secureaudit_system:secureaudit_system_pass@localhost:5432/secureaudit_test")
os.environ.setdefault("APP_DEBUG", "false")

from app.core.config import settings  # noqa: E402
from app.db.base import Base  # noqa: E402
from app.db.session import SessionLocal, SystemSessionLocal  # noqa: E402
from app.main import app as fastapi_app  # noqa: E402
import app.models  # noqa: E402, F401


def _apply_schema() -> None:
    """Crea tablas + RLS + políticas directamente (sin Alembic)."""

    system_engine = create_engine(settings.SYSTEM_DATABASE_URL)
    with system_engine.connect() as conn:
        # 1. Limpiar schema (drop tables + functions + sequences)
        conn.execute(text("""
            DO $$
            DECLARE r RECORD;
            BEGIN
                FOR r IN SELECT tablename FROM pg_tables WHERE schemaname = 'public'
                LOOP
                    EXECUTE 'DROP TABLE IF EXISTS public.' || quote_ident(r.tablename) || ' CASCADE';
                END LOOP;
                FOR r IN SELECT sequence_name FROM information_schema.sequences WHERE sequence_schema = 'public'
                LOOP
                    EXECUTE 'DROP SEQUENCE IF EXISTS public.' || quote_ident(r.sequence_name) || ' CASCADE';
                END LOOP;
                FOR r IN SELECT routine_name FROM information_schema.routines
                         WHERE routine_schema = 'public' AND routine_type = 'FUNCTION'
                LOOP
                    EXECUTE 'DROP FUNCTION IF EXISTS public.' || quote_ident(r.routine_name) || ' CASCADE';
                END LOOP;
            END $$;
        """))

        # 2. Crear tablas con metadata
        Base.metadata.create_all(bind=conn)

        # 3. Crear funciones RLS
        conn.execute(text("""
            CREATE OR REPLACE FUNCTION current_app_user() RETURNS uuid AS $$
            BEGIN
                RETURN current_setting('app.current_user', true)::uuid;
            EXCEPTION
                WHEN OTHERS THEN RETURN NULL;
            END;
            $$ LANGUAGE plpgsql STABLE;
        """))

        conn.execute(text("""
            CREATE OR REPLACE FUNCTION is_member_of(org_id uuid) RETURNS boolean
            SECURITY DEFINER
            SET search_path = public
            AS $$
            BEGIN
                RETURN EXISTS (
                    SELECT 1 FROM memberships
                    WHERE memberships.organization_id = org_id
                      AND memberships.user_id = current_app_user()
                );
            END;
            $$ LANGUAGE plpgsql STABLE;
        """))

        # 4. RLS en las 3 tablas
        for table in ["organizations", "memberships", "users"]:
            conn.execute(text(f"ALTER TABLE {table} ENABLE ROW LEVEL SECURITY"))
            conn.execute(text(f"ALTER TABLE {table} FORCE ROW LEVEL SECURITY"))

        # 5. Políticas de users y memberships
        conn.execute(text("""
            CREATE POLICY users_isolation ON users
            FOR ALL USING (id = current_app_user());
        """))
        conn.execute(text("""
            CREATE POLICY memberships_isolation ON memberships
            FOR ALL USING (user_id = current_app_user());
        """))

        # 6. Políticas de organizations (split por operación)
        conn.execute(text("""
            CREATE POLICY organizations_select ON organizations
            FOR SELECT USING (is_member_of(id));
        """))
        conn.execute(text("""
            CREATE POLICY organizations_insert ON organizations
            FOR INSERT WITH CHECK (true);
        """))
        conn.execute(text("""
            CREATE POLICY organizations_update ON organizations
            FOR UPDATE USING (is_member_of(id))
            WITH CHECK (is_member_of(id));
        """))
        conn.execute(text("""
            CREATE POLICY organizations_delete ON organizations
            FOR DELETE USING (is_member_of(id));
        """))

        # 7. Permisos al rol de app
        conn.execute(text("GRANT ALL ON ALL TABLES IN SCHEMA public TO secureaudit"))
        conn.execute(text("GRANT ALL ON ALL SEQUENCES IN SCHEMA public TO secureaudit"))
        conn.execute(text("GRANT ALL ON ALL FUNCTIONS IN SCHEMA public TO secureaudit"))

        conn.commit()

    system_engine.dispose()


@pytest.fixture(scope="session", autouse=True)
def setup_test_database() -> Generator[None, None, None]:
    """Aplica el esquema completo a la BD de test."""
    _apply_schema()
    yield
    # Teardown: limpiar
    system_engine = create_engine(settings.SYSTEM_DATABASE_URL)
    with system_engine.connect() as conn:
        conn.execute(text("""
            DO $$
            DECLARE r RECORD;
            BEGIN
                FOR r IN SELECT tablename FROM pg_tables WHERE schemaname = 'public'
                LOOP
                    EXECUTE 'DROP TABLE IF EXISTS public.' || quote_ident(r.tablename) || ' CASCADE';
                END LOOP;
            END $$;
        """))
        conn.commit()
    system_engine.dispose()


@pytest.fixture(autouse=True)
def clean_tables() -> Generator[None, None, None]:
    """Limpia las tablas Y el contexto RLS antes de cada test."""
    db: Session = SystemSessionLocal()
    try:
        db.execute(text(
            "TRUNCATE memberships, users, organizations RESTART IDENTITY CASCADE"
        ))
        db.execute(text("SELECT set_config('app.current_user', '', false)"))
        db.commit()
    finally:
        db.close()
    yield


@pytest.fixture
def db() -> Generator[Session, None, None]:
    """Sesión normal (con RLS)."""
    session = SessionLocal()
    try:
        yield session
    finally:
        session.rollback()
        session.close()


@pytest.fixture
def system_db() -> Generator[Session, None, None]:
    """Sesión de sistema (BYPASSRLS)."""
    session = SystemSessionLocal()
    try:
        yield session
    finally:
        session.rollback()
        session.close()


@pytest.fixture
def client() -> Generator[TestClient, None, None]:
    """Cliente de test de FastAPI."""
    with TestClient(fastapi_app) as c:
        yield c
