"""Utilidades para el contexto RLS de PostgreSQL.

El contexto se establece con `set_config(..., true)` (LOCAL a la transacción).
Es importante que el consumidor mantenga la transacción abierta mientras
hace las queries protegidas, y haga commit/rollback al final.
"""

from uuid import UUID

from sqlalchemy import text
from sqlalchemy.orm import Session


def set_rls_context(db: Session, user_id: UUID | str | None) -> None:
    """Establece el contexto RLS para la transacción actual.

    IMPORTANTE: no hace commit. El caller decide cuándo cerrar la transacción.
    """
    if user_id:
        db.execute(
            text("SELECT set_config('app.current_user', :uid, true)"),
            {"uid": str(user_id)},
        )
    else:
        db.execute(text("SELECT set_config('app.current_user', '', true)"))


def clear_rls_context(db: Session) -> None:
    """Limpia el contexto RLS (LOCAL a la transacción)."""
    db.execute(text("SELECT set_config('app.current_user', '', true)"))
