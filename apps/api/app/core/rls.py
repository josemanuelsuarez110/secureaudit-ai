"""Utilidades para el contexto RLS de PostgreSQL.

IMPORTANTE: el contexto debe establecerse en una transacción
para que no se filtre entre requests.
"""

from uuid import UUID

from sqlalchemy import text
from sqlalchemy.orm import Session


def set_rls_context(db: Session, user_id: UUID | str | None) -> None:
    """Establece el contexto RLS para la transacción actual.

    Debe llamarse DENTRO de una transacción activa (con SET LOCAL).
    Si user_id es None, el contexto se limpia (RLS bloquea todo).
    """
    if user_id:
        db.execute(
            text("SELECT set_config('app.current_user', :uid, true)"),
            {"uid": str(user_id)},
        )
    else:
        db.execute(
            text("SELECT set_config('app.current_user', '', true)")
        )


def clear_rls_context(db: Session) -> None:
    """Limpia el contexto RLS (útil al final de un request)."""
    db.execute(text("SELECT set_config('app.current_user', '', true)"))
