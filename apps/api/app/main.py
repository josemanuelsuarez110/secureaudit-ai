"""SecureAudit AI — API principal."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(
    title="SecureAudit AI",
    description="SaaS B2B de auditoría continua de seguridad",
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS (ajustar en producción)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


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
