import uuid
from collections.abc import Sequence
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.utils import parse_datetime_param
from app.crud import access_event as crud_access_event
from app.crud import model as crud_model
from app.crud import user as crud_user
from app.schemas.access_event import AccessEventCreate, AccessEventRead

router = APIRouter(prefix="/access-events", tags=["Access Events"])


@router.get("", response_model=list[AccessEventRead], summary="List access events with filters")
async def list_access_events(
    user_id: uuid.UUID | None = Query(None, description="Filter by user ID"),
    model_id: uuid.UUID | None = Query(None, description="Filter by ML model ID"),
    start_time: str | None = Query(None, description="Filter events occurring on or after this timestamp (ISO format)"),
    end_time: str | None = Query(None, description="Filter events occurring on or before this timestamp (ISO format)"),
    skip: int = Query(0, ge=0, description="Offset for pagination"),
    limit: int = Query(100, ge=1, le=500, description="Maximum number of items to return"),
    db: AsyncSession = Depends(get_db),
) -> Sequence[AccessEventRead]:
    parsed_start = parse_datetime_param(start_time)
    parsed_end = parse_datetime_param(end_time)
    events = await crud_access_event.get_access_events(
        db=db,
        user_id=user_id,
        model_id=model_id,
        start_time=parsed_start,
        end_time=parsed_end,
        skip=skip,
        limit=limit,
    )
    return events


@router.get("/{event_id}", response_model=AccessEventRead, summary="Get single access event by ID")
async def get_access_event(
    event_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
) -> AccessEventRead:
    event = await crud_access_event.get_access_event_by_id(db, event_id=event_id)
    if not event:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Access event with id '{event_id}' not found",
        )
    return event


@router.post("", response_model=AccessEventRead, status_code=status.HTTP_201_CREATED, summary="Ingest single access event")
async def ingest_access_event(
    event_in: AccessEventCreate,
    db: AsyncSession = Depends(get_db),
) -> AccessEventRead:
    if event_in.user_id is not None:
        user = await crud_user.get_user_by_id(db, user_id=event_in.user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"User with id '{event_in.user_id}' not found",
            )
    model = await crud_model.get_model_by_id(db, model_id=event_in.model_id)
    if not model:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Model with id '{event_in.model_id}' not found",
        )

    return await crud_access_event.create_access_event(db, event_in=event_in)
