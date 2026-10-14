"""enable row level security on all tables

Revision ID: rls_001
Revises: d88289f8cb74
Create Date: 2026-10-14 16:45:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'rls_001'
down_revision: Union[str, None] = 'd88289f8cb74'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Aplicar RLS en todas las tablas multi-tenant."""

    # 1. Función helper: obtener el user_id actual desde el setting
    op.execute("""
        CREATE OR REPLACE FUNCTION current_app_user() RETURNS uuid AS $$
        BEGIN
            RETURN current_setting('app.current_user', true)::uuid;
        EXCEPTION
            WHEN OTHERS THEN RETURN NULL;
        END;
        $$ LANGUAGE plpgsql STABLE;
    """)

    # 2. Función helper con SECURITY DEFINER para evitar circularidad
    #    Permite verificar si un usuario pertenece a una organización
    #    SIN activar RLS en memberships (evita recursión infinita)
    op.execute("""
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
    """)

    # 3. Activar RLS en organizations
    op.execute("ALTER TABLE organizations ENABLE ROW LEVEL SECURITY;")
    op.execute("ALTER TABLE organizations FORCE ROW LEVEL SECURITY;")
    op.execute("""
        CREATE POLICY organizations_isolation ON organizations
        FOR ALL
        USING (is_member_of(id));
    """)

    # 4. Activar RLS en memberships
    op.execute("ALTER TABLE memberships ENABLE ROW LEVEL SECURITY;")
    op.execute("ALTER TABLE memberships FORCE ROW LEVEL SECURITY;")
    op.execute("""
        CREATE POLICY memberships_isolation ON memberships
        FOR ALL
        USING (user_id = current_app_user());
    """)

    # 5. Activar RLS en users
    op.execute("ALTER TABLE users ENABLE ROW LEVEL SECURITY;")
    op.execute("ALTER TABLE users FORCE ROW LEVEL SECURITY;")
    op.execute("""
        CREATE POLICY users_isolation ON users
        FOR ALL
        USING (id = current_app_user());
    """)


def downgrade() -> None:
    """Revertir RLS."""

    # Revertir users
    op.execute("DROP POLICY IF EXISTS users_isolation ON users;")
    op.execute("ALTER TABLE users DISABLE ROW LEVEL SECURITY;")

    # Revertir memberships
    op.execute("DROP POLICY IF EXISTS memberships_isolation ON memberships;")
    op.execute("ALTER TABLE memberships DISABLE ROW LEVEL SECURITY;")

    # Revertir organizations
    op.execute("DROP POLICY IF EXISTS organizations_isolation ON organizations;")
    op.execute("ALTER TABLE organizations DISABLE ROW LEVEL SECURITY;")

    # Eliminar funciones helper
    op.execute("DROP FUNCTION IF EXISTS is_member_of(uuid);")
    op.execute("DROP FUNCTION IF EXISTS current_app_user();")
