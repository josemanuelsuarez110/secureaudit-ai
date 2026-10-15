"""SecureAudit AI — API principal."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1 import api_router
from app.core.config import settings

app = FastAPI(
    title=settings.APP_NAME,
    description="SaaS B2B de auditoría continua de seguridad",
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Router principal
app.include_router(api_router)


@app.get("/", tags=["root"])
async def root():
    """Endpoint raíz."""
    return {
        "service": "secureaudit-ai",
        "version": "0.1.0",
        "status": "ok",
    }


@app.get("/health", tags=["health"])
async def health():
    """Healthcheck para monitoreo."""
    return {
        "status": "healthy",
        "service": "secureaudit-ai-api",
    }
