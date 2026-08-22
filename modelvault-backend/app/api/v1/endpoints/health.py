from fastapi import APIRouter
from app.schemas.health import RootHealthResponse, DetailedHealthResponse
from app.core.config import settings
from app.core.database import check_db_connection

router = APIRouter()


@router.get("/health", response_model=DetailedHealthResponse, tags=["Health"])
async def get_v1_health():
    db_connected = await check_db_connection()
    return DetailedHealthResponse(
        status="ok" if db_connected else "degraded",
        service=settings.PROJECT_NAME.lower(),
        version=settings.VERSION,
        database="connected" if db_connected else "disconnected"
    )
