"""Loop principal del scanner worker."""

import logging
import signal
import sys
import time
from datetime import datetime, timezone

from worker.checks.dns import check_dns
from worker.checks.http import check_http
from worker.checks.tls import check_tls
from worker.config import settings
from worker.db import (
    claim_next_job,
    complete_job,
    fail_job,
    get_asset_domain,
    get_session,
    save_result,
)


logging.basicConfig(
    level=logging.DEBUG if settings.DEBUG else logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("worker")


# Flag para shutdown graceful
_shutdown = False


def _handle_signal(signum, frame):
    global _shutdown
    logger.info(f"Señal {signum} recibida. Terminando después del job actual...")
    _shutdown = True


def process_job(job: dict) -> None:
    """Procesa un scan job completo."""
    job_id = job["id"]
    org_id = job["organization_id"]
    asset_id = job["asset_id"]
    scan_type = job["scan_type"]

    logger.info(f"Procesando job {job_id} (asset {asset_id}, tipo {scan_type})")

    with get_session() as session:
        domain = get_asset_domain(session, asset_id)

        if not domain:
            logger.warning(f"Asset {asset_id} no encontrado o no está activo")
            fail_job(session, job_id, "Asset no encontrado o no está activo")
            return

        logger.info(f"Dominio: {domain}")

        all_findings = []

        # Ejecutar checks según scan_type
        if scan_type in ("full", "tls"):
            logger.info(f"  → Checks TLS")
            try:
                all_findings.extend(check_tls(domain, settings.CHECK_TIMEOUT))
            except Exception as exc:
                logger.exception(f"Error en checks TLS: {exc}")

        if scan_type in ("full", "http"):
            logger.info(f"  → Checks HTTP")
            try:
                all_findings.extend(check_http(domain, settings.CHECK_TIMEOUT))
            except Exception as exc:
                logger.exception(f"Error en checks HTTP: {exc}")

        if scan_type in ("full", "dns"):
            logger.info(f"  → Checks DNS")
            try:
                all_findings.extend(check_dns(domain, settings.CHECK_TIMEOUT))
            except Exception as exc:
                logger.exception(f"Error en checks DNS: {exc}")

        # Guardar resultados
        logger.info(f"  → Guardando {len(all_findings)} findings")
        for finding in all_findings:
            save_result(
                session,
                organization_id=org_id,
                scan_job_id=job_id,
                asset_id=asset_id,
                **finding,
            )

        # Marcar job completado
        complete_job(session, job_id)
        logger.info(f"✓ Job {job_id} completado ({len(all_findings)} findings)")


def run_worker() -> None:
    """Loop principal del worker."""
    logger.info(f"Worker {settings.WORKER_ID} arrancando...")
    logger.info(f"Poll interval: {settings.POLL_INTERVAL_SECONDS}s")

    while not _shutdown:
        try:
            with get_session() as session:
                job = claim_next_job(session)

            if job is None:
                # No hay jobs, esperar
                time.sleep(settings.POLL_INTERVAL_SECONDS)
                continue

            # Procesar el job (fuera del context manager)
            process_job(job)

        except KeyboardInterrupt:
            logger.info("Ctrl+C recibido")
            break
        except Exception as exc:
            logger.exception(f"Error en el loop: {exc}")
            time.sleep(settings.POLL_INTERVAL_SECONDS)

    logger.info("Worker detenido")


def main() -> None:
    """Entry point del worker."""
    signal.signal(signal.SIGINT, _handle_signal)
    signal.signal(signal.SIGTERM, _handle_signal)

    try:
        run_worker()
    except Exception as exc:
        logger.exception(f"Fatal: {exc}")
        sys.exit(1)


if __name__ == "__main__":
    main()
