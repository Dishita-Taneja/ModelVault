from contextlib import asynccontextmanager
from typing import Any
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import api_router
from app.core.config import settings


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Application startup logic (if any)
    yield
    # Application shutdown logic (if any)


app = FastAPI(
    title=settings.PROJECT_NAME,
    description="ModelVault Backend & API Layer — ML Model Access Security Incident Response",
    version="0.1.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount all API routes
app.include_router(api_router, prefix=settings.API_V1_STR)


@app.get("/health", tags=["Health"], summary="Health check")
async def health_check() -> dict[str, str]:
    return {"status": "ok", "service": "modelvault-backend"}
