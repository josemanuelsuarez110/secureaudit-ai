"""split organizations policies by operation

Revision ID: split_org_policies
Revises: rls_001
Create Date: 2026-10-16 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op


revision: str = 'split_org_policies'
down_revision: Union[str, None] = 'rls_001'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Separar la política de organizations por operación."""
    # Eliminar política actual (FOR ALL)
    op.execute("DROP POLICY IF EXISTS organizations_isolation ON organizations;")

    # SELECT: solo ver donde soy miembro
    op.execute("""
        CREATE POLICY organizations_select ON organizations
        FOR SELECT USING (is_member_of(id));
    """)

    # INSERT: permitir crear (el membership se crea después)
    op.execute("""
        CREATE POLICY organizations_insert ON organizations
        FOR INSERT WITH CHECK (true);
    """)

    # UPDATE: solo miembro
    op.execute("""
        CREATE POLICY organizations_update ON organizations
        FOR UPDATE USING (is_member_of(id))
        WITH CHECK (is_member_of(id));
    """)

    # DELETE: solo miembro
    op.execute("""
        CREATE POLICY organizations_delete ON organizations
        FOR DELETE USING (is_member_of(id));
    """)


def downgrade() -> None:
    """Revertir."""
    op.execute("DROP POLICY IF EXISTS organizations_select ON organizations;")
    op.execute("DROP POLICY IF EXISTS organizations_insert ON organizations;")
    op.execute("DROP POLICY IF EXISTS organizations_update ON organizations;")
    op.execute("DROP POLICY IF EXISTS organizations_delete ON organizations;")
    op.execute("""
        CREATE POLICY organizations_isolation ON organizations
        FOR ALL USING (is_member_of(id));
    """)
