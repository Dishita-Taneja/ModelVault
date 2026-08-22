import datetime
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.core.database import get_db
from app.models.suspicious_event import SuspiciousEvent
from app.schemas.suspicious_event import SuspiciousEventResponse
from app.core.exceptions import ResourceNotFoundError

router = APIRouter()


@router.get("", response_model=List[SuspiciousEventResponse], tags=["Suspicious Events"])
@router.get("/", response_model=List[SuspiciousEventResponse], tags=["Suspicious Events"])
async def list_suspicious_events(
    user_id: Optional[str] = Query(None, description="Filter by User ID"),
    user: Optional[str] = Query(None, description="Filter by User ID/Name alias"),
    model_id: Optional[str] = Query(None, description="Filter by Model ID"),
    model: Optional[str] = Query(None, description="Filter by Model ID alias"),
    severity: Optional[str] = Query(None, description="Filter by severity: LOW, MEDIUM, HIGH, CRITICAL"),
    exfiltration_suspected: Optional[bool] = Query(None, description="Filter by exfiltration flag"),
    start_time: Optional[datetime.datetime] = Query(None, description="Filter events after start_time"),
    end_time: Optional[datetime.datetime] = Query(None, description="Filter events before end_time"),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    db: AsyncSession = Depends(get_db)
):
    """Retrieves suspicious events with filtering by user, model, severity, time range, exfiltration flag, and pagination."""
    query = select(SuspiciousEvent)

    target_user = user_id or user
    if target_user:
        query = query.where(SuspiciousEvent.user_id == target_user)

    target_model = model_id or model
    if target_model:
        query = query.where(SuspiciousEvent.model_id == target_model)

    if severity:
        query = query.where(SuspiciousEvent.severity == severity.upper())

    if exfiltration_suspected is not None:
        query = query.where(SuspiciousEvent.weight_exfiltration_suspected == exfiltration_suspected)

    if start_time:
        query = query.where(SuspiciousEvent.timestamp >= start_time)

    if end_time:
        query = query.where(SuspiciousEvent.timestamp <= end_time)

    query = query.order_by(SuspiciousEvent.risk_score.desc()).offset(skip).limit(limit)
    res = await db.execute(query)
    return list(res.scalars().all())


@router.get("/top", response_model=List[SuspiciousEventResponse], tags=["Suspicious Events"])
async def get_top_suspicious_events(
    limit: int = Query(3, ge=1, le=10),
    db: AsyncSession = Depends(get_db)
):
    """Retrieves top N highest risk suspicious events. Returns exactly 3 events when at least 3 exist."""
    res = await db.execute(select(SuspiciousEvent).order_by(SuspiciousEvent.risk_score.desc()).limit(limit))
    return list(res.scalars().all())


@router.get("/{id}", response_model=SuspiciousEventResponse, tags=["Suspicious Events"])
async def get_suspicious_event_detail(id: str, db: AsyncSession = Depends(get_db)):
    """Retrieves complete suspicious event record including full evidence chain and investigation timeline."""
    res = await db.execute(select(SuspiciousEvent).where(SuspiciousEvent.event_id == id))
    se_obj = res.scalars().first()
    if not se_obj:
        raise ResourceNotFoundError(resource="SuspiciousEvent", identifier=id)
    return se_obj
