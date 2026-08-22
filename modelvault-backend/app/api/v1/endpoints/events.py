import datetime
from typing import List, Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.core.database import get_db
from app.models.event import NormalizedEvent
from app.schemas.event import NormalizedEventResponse, NormalizedEventCreate
from app.crud import crud_event
from app.core.exceptions import ResourceNotFoundError

router = APIRouter()


@router.get("", response_model=List[NormalizedEventResponse], tags=["Events"])
@router.get("/", response_model=List[NormalizedEventResponse], tags=["Events"])
async def list_events(
    user_id: Optional[str] = Query(None, description="Filter by User ID"),
    model_id: Optional[str] = Query(None, description="Filter by Model ID"),
    source: Optional[str] = Query(None, description="Filter by log source: IAM, EC2, S3, MODEL"),
    start_time: Optional[datetime.datetime] = Query(None, description="Filter events after start_time"),
    end_time: Optional[datetime.datetime] = Query(None, description="Filter events before end_time"),
    anomaly_only: Optional[bool] = Query(None, description="Filter anomalous events only"),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    db: AsyncSession = Depends(get_db)
):
    """Retrieves normalized cloud and model access events with comprehensive filtering and pagination."""
    query = select(NormalizedEvent)

    if user_id:
        query = query.where(NormalizedEvent.user_id == user_id)
    if model_id:
        query = query.where(NormalizedEvent.model_id == model_id)
    if source:
        query = query.where(NormalizedEvent.source == source.upper())
    if anomaly_only:
        query = query.where(NormalizedEvent.anomaly_flag == True)
    if start_time:
        query = query.where(NormalizedEvent.event_time_reconciled >= start_time)
    if end_time:
        query = query.where(NormalizedEvent.event_time_reconciled <= end_time)

    query = query.order_by(NormalizedEvent.event_time_reconciled.asc()).offset(skip).limit(limit)
    res = await db.execute(query)
    return list(res.scalars().all())


@router.get("/{id}", response_model=NormalizedEventResponse, tags=["Events"])
async def get_event(id: str, db: AsyncSession = Depends(get_db)):
    """Retrieves single normalized event by ID."""
    event = await crud_event.get_event_by_id(db, event_id=id)
    if not event:
        raise ResourceNotFoundError(resource="NormalizedEvent", identifier=id)
    return event


@router.post("", response_model=NormalizedEventResponse, status_code=201, tags=["Events"])
@router.post("/", response_model=NormalizedEventResponse, status_code=201, tags=["Events"])
async def create_event(event_in: NormalizedEventCreate, db: AsyncSession = Depends(get_db)):
    """Creates a normalized event record."""
    return await crud_event.create_event(db, event_in=event_in)
