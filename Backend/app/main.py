from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError

from app.core.config import settings
from app.core.logging import logger
from app.core.database import engine, Base
from app.core.exceptions import ModelVaultError
from app.core.error_handlers import (
    modelvault_exception_handler,
    http_exception_handler,
    validation_exception_handler
)
from app.schemas.health import RootHealthResponse
from app.api.v1.api import api_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info(f"Starting {settings.PROJECT_NAME} backend service...")
    # Initialize database tables for local dev / testing if engine connects
    try:
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        logger.info("Database connection and tables initialized.")
    except Exception as e:
        logger.warning(f"Database initialization deferred: {e}")
    
    yield
    
    logger.info("Shutting down backend service...")
    await engine.dispose()


app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

# CORS Configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register Exception Handlers
app.add_exception_handler(ModelVaultError, modelvault_exception_handler)
app.add_exception_handler(HTTPException, http_exception_handler)
app.add_exception_handler(RequestValidationError, validation_exception_handler)


# Root Health Check Endpoint (Exact PRD requirement)
@app.get("/health", response_model=RootHealthResponse, tags=["Health"])
async def root_health():
    return RootHealthResponse(status="ok", service="modelvault")


# API Version 1 Router
app.include_router(api_router, prefix=settings.API_V1_STR)
