
from app.core.database import get_db
from app.crud import crud_alert
from app.schemas.alert import AlertCreate, AlertResponse
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter()


@router.get("/top-suspicious", response_model=list[AlertResponse])
async def get_top_suspicious_events(limit: int = 3, db: AsyncSession = Depends(get_db)):
    """Exposes top 3 suspicious events / alerts as required by PRD item 8."""
    return await crud_alert.get_top_suspicious_events(db, limit=limit)


@router.post("/", response_model=AlertResponse, status_code=201)
async def create_alert(alert_in: AlertCreate, db: AsyncSession = Depends(get_db)):
    return await crud_alert.create_alert(db, alert_in=alert_in)
