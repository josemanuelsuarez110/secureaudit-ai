"""Tests de aislamiento multi-tenant (Row-Level Security)."""

import pytest
from sqlalchemy import select, text
from sqlalchemy.orm import Session

from app.core.rls import set_rls_context
from app.models import Membership, Organization, User


# =========================================================
# Fixture: crear 2 organizaciones + 2 usuarios + 2 memberships
# =========================================================

@pytest.fixture
def sample_data(system_db: Session) -> dict:
    """Crea datos de prueba: 2 organizaciones con 1 usuario cada una."""
    # Organizaciones
    org_a = Organization(name="Empresa A", slug="empresa-a")
    org_b = Organization(name="Empresa B", slug="empresa-b")
    system_db.add_all([org_a, org_b])
    system_db.flush()

    # Usuarios
    user_a = User(
        email="user-a@test.com",
        hashed_password="fake_hash_a",
        full_name="User A",
        is_active=True,
        is_superuser=False,
    )
    user_b = User(
        email="user-b@test.com",
        hashed_password="fake_hash_b",
        full_name="User B",
        is_active=True,
        is_superuser=False,
    )
    system_db.add_all([user_a, user_b])
    system_db.flush()

    # Memberships
    membership_a = Membership(
        user_id=user_a.id,
        organization_id=org_a.id,
        role="admin",
    )
    membership_b = Membership(
        user_id=user_b.id,
        organization_id=org_b.id,
        role="admin",
    )
    system_db.add_all([membership_a, membership_b])
    system_db.commit()

    return {
        "org_a": org_a,
        "org_b": org_b,
        "user_a": user_a,
        "user_b": user_b,
        "membership_a": membership_a,
        "membership_b": membership_b,
    }


# =========================================================
# Tests de aislamiento
# =========================================================

def test_user_a_sees_only_own_user(db: Session, sample_data: dict) -> None:
    """User A solo ve su propio registro en `users`."""
    set_rls_context(db, sample_data["user_a"].id)

    users = db.execute(select(User)).scalars().all()

    assert len(users) == 1
    assert users[0].id == sample_data["user_a"].id
    assert users[0].email == "user-a@test.com"


def test_user_b_sees_only_own_user(db: Session, sample_data: dict) -> None:
    """User B solo ve su propio registro en `users`."""
    set_rls_context(db, sample_data["user_b"].id)

    users = db.execute(select(User)).scalars().all()

    assert len(users) == 1
    assert users[0].id == sample_data["user_b"].id
    assert users[0].email == "user-b@test.com"


def test_user_a_sees_only_own_membership(db: Session, sample_data: dict) -> None:
    """User A solo ve su propio membership."""
    set_rls_context(db, sample_data["user_a"].id)

    memberships = db.execute(select(Membership)).scalars().all()

    assert len(memberships) == 1
    assert memberships[0].user_id == sample_data["user_a"].id
    assert memberships[0].organization_id == sample_data["org_a"].id


def test_user_a_sees_only_own_organization(db: Session, sample_data: dict) -> None:
    """User A solo ve la organización a la que pertenece."""
    set_rls_context(db, sample_data["user_a"].id)

    orgs = db.execute(select(Organization)).scalars().all()

    assert len(orgs) == 1
    assert orgs[0].id == sample_data["org_a"].id
    assert orgs[0].name == "Empresa A"


def test_user_b_sees_only_own_organization(db: Session, sample_data: dict) -> None:
    """User B solo ve la organización a la que pertenece."""
    set_rls_context(db, sample_data["user_b"].id)

    orgs = db.execute(select(Organization)).scalars().all()

    assert len(orgs) == 1
    assert orgs[0].id == sample_data["org_b"].id
    assert orgs[0].name == "Empresa B"


def test_no_context_sees_nothing(db: Session, sample_data: dict) -> None:
    """Sin contexto RLS, no se ve nada."""
    # Sin set_rls_context
    users = db.execute(select(User)).scalars().all()
    memberships = db.execute(select(Membership)).scalars().all()
    orgs = db.execute(select(Organization)).scalars().all()

    assert len(users) == 0
    assert len(memberships) == 0
    assert len(orgs) == 0


def test_system_bypasses_rls(system_db: Session, sample_data: dict) -> None:
    """El rol de sistema ve TODOS los datos (BYPASSRLS)."""
    users = system_db.execute(select(User)).scalars().all()
    memberships = system_db.execute(select(Membership)).scalars().all()
    orgs = system_db.execute(select(Organization)).scalars().all()

    assert len(users) == 2
    assert len(memberships) == 2
    assert len(orgs) == 2


def test_is_member_of_function(db: Session, sample_data: dict) -> None:
    """La función is_member_of devuelve True/False correctamente."""
    set_rls_context(db, sample_data["user_a"].id)

    # User A es miembro de Org A
    result = db.execute(
        text("SELECT is_member_of(:org_id)"),
        {"org_id": str(sample_data["org_a"].id)},
    ).scalar()
    assert result is True

    # User A NO es miembro de Org B
    result = db.execute(
        text("SELECT is_member_of(:org_id)"),
        {"org_id": str(sample_data["org_b"].id)},
    ).scalar()
    assert result is False
