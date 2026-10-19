"""Configuración del scanner worker."""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Settings cargados desde variables de entorno."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    DATABASE_URL: str = (
        "postgresql+psycopg://secureaudit_system:"
        "secureaudit_system_pass@localhost:5432/secureaudit_dev"
    )

    WORKER_ID: str = "worker-1"
    POLL_INTERVAL_SECONDS: int = 5
    MAX_JOBS_PER_CYCLE: int = 1

    CHECK_TIMEOUT: int = 10
    JOB_TIMEOUT: int = 60

    HTTP_MAX_REDIRECTS: int = 5
    HTTP_MAX_SIZE_BYTES: int = 1_000_000
    HTTP_USER_AGENT: str = "SecureAuditAI-Scanner/0.1"

    DEBUG: bool = False


settings = Settings()
