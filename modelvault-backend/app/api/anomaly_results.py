import uuid
from collections.abc import Sequence
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.utils import parse_datetime_param
from app.crud import anomaly_result as crud_anomaly_result
from app.crud import access_event as crud_access_event
from app.schemas.anomaly_result import AnomalyResultCreate, AnomalyResultRead

router = APIRouter(prefix="/anomaly-results", tags=["Anomaly Results"])


@router.get("", response_model=list[AnomalyResultRead], summary="List flagged anomaly results with filters")
async def list_anomaly_results(
    user_id: uuid.UUID | None = Query(None, description="Filter by user ID associated with the access event"),
    model_id: uuid.UUID | None = Query(None, description="Filter by ML model ID associated with the access event"),
    start_time: str | None = Query(None, description="Filter results for events occurring on or after this timestamp (ISO format)"),
    end_time: str | None = Query(None, description="Filter results for events occurring on or before this timestamp (ISO format)"),
    skip: int = Query(0, ge=0, description="Offset for pagination"),
    limit: int = Query(100, ge=1, le=500, description="Maximum number of items to return"),
    db: AsyncSession = Depends(get_db),
) -> Sequence[AnomalyResultRead]:
    parsed_start = parse_datetime_param(start_time)
    parsed_end = parse_datetime_param(end_time)
    results = await crud_anomaly_result.get_anomaly_results(
        db=db,
        user_id=user_id,
        model_id=model_id,
        start_time=parsed_start,
        end_time=parsed_end,
        skip=skip,
        limit=limit,
    )
    return results


@router.get("/{result_id}", response_model=AnomalyResultRead, summary="Get single anomaly result by ID")
async def get_anomaly_result(
    result_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
) -> AnomalyResultRead:
    result = await crud_anomaly_result.get_anomaly_result_by_id(db, result_id=result_id)
    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Anomaly result with id '{result_id}' not found",
        )
    return result


@router.post("", response_model=AnomalyResultRead, status_code=status.HTTP_201_CREATED, summary="Ingest anomaly result payload")
async def create_anomaly_result(
    result_in: AnomalyResultCreate,
    db: AsyncSession = Depends(get_db),
) -> AnomalyResultRead:
    access_event = await crud_access_event.get_access_event_by_id(db, event_id=result_in.access_event_id)
    if not access_event:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Access event with id '{result_in.access_event_id}' not found",
        )
    return await crud_anomaly_result.create_anomaly_result(db, result_in=result_in)
