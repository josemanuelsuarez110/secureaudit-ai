"""Conexión a PostgreSQL para el worker."""

import json
from contextlib import contextmanager
from typing import Generator

from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session, sessionmaker

from worker.config import settings


engine = create_engine(
    settings.DATABASE_URL,
    pool_pre_ping=True,
    echo=settings.DEBUG,
)

SessionLocal = sessionmaker(
    bind=engine,
    autocommit=False,
    autoflush=False,
    expire_on_commit=False,
)


@contextmanager
def get_session() -> Generator[Session, None, None]:
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()


def claim_next_job(session: Session) -> dict | None:
    result = session.execute(text("""
        UPDATE scan_jobs
        SET status = 'running', started_at = NOW(), updated_at = NOW()
        WHERE id = (
            SELECT id FROM scan_jobs
            WHERE status = 'pending'
            ORDER BY priority ASC, created_at ASC
            LIMIT 1
            FOR UPDATE SKIP LOCKED
        )
        RETURNING id, organization_id, asset_id, scan_type
    """))
    row = result.fetchone()
    session.commit()
    if not row:
        return None
    return {
        "id": row.id,
        "organization_id": row.organization_id,
        "asset_id": row.asset_id,
        "scan_type": row.scan_type,
    }


def get_asset_domain(session: Session, asset_id) -> str | None:
    result = session.execute(
        text("SELECT domain, status FROM assets WHERE id = :id"),
        {"id": asset_id},
    )
    row = result.fetchone()
    if not row or row.status != "active":
        return None
    return row.domain


def complete_job(session: Session, job_id) -> None:
    session.execute(
        text("""
            UPDATE scan_jobs
            SET status = 'completed', completed_at = NOW(), updated_at = NOW()
            WHERE id = :id
        """),
        {"id": job_id},
    )
    session.commit()


def fail_job(session: Session, job_id, error_message: str) -> None:
    session.execute(
        text("""
            UPDATE scan_jobs
            SET status = 'failed', completed_at = NOW(),
                error_message = :error, updated_at = NOW()
            WHERE id = :id
        """),
        {"id": job_id, "error": error_message[:500]},
    )
    session.commit()


def save_result(
    session: Session,
    organization_id,
    scan_job_id,
    asset_id,
    category: str,
    check_name: str,
    status: str,
    severity: str,
    title: str,
    description: str | None = None,
    evidence: dict | None = None,
    recommendation: str | None = None,
) -> None:
    session.execute(
        text("""
            INSERT INTO scan_results (
                id, organization_id, scan_job_id, asset_id,
                category, check_name, status, severity, title,
                description, evidence, recommendation
            )
            VALUES (
                gen_random_uuid(), :organization_id, :scan_job_id, :asset_id,
                :category, :check_name, :status, :severity, :title,
                :description, :evidence, :recommendation
            )
        """),
        {
            "organization_id": organization_id,
            "scan_job_id": scan_job_id,
            "asset_id": asset_id,
            "category": category,
            "check_name": check_name,
            "status": status,
            "severity": severity,
            "title": title,
            "description": description,
            "evidence": json.dumps(evidence) if evidence else None,
            "recommendation": recommendation,
        },
    )
    session.commit()
