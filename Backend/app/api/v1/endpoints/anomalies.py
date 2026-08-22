from typing import List, Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.core.database import get_db
from app.models.anomaly_result import AnomalyResult
from app.schemas.ml import AnomalyResultResponse

router = APIRouter()


@router.get("", response_model=List[AnomalyResultResponse], tags=["Anomalies"])
@router.get("/", response_model=List[AnomalyResultResponse], tags=["Anomalies"])
async def list_anomalies(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    anomalous_only: bool = Query(False, description="Filter anomalous events only"),
    db: AsyncSession = Depends(get_db)
):
    """Retrieves ML anomaly detection results with optional filtering and pagination."""
    query = select(AnomalyResult)
    if anomalous_only:
        query = query.where(AnomalyResult.is_anomaly == True)
    query = query.order_by(AnomalyResult.anomaly_score.desc()).offset(skip).limit(limit)
    res = await db.execute(query)
    return list(res.scalars().all())


@router.get("/top", response_model=List[AnomalyResultResponse], tags=["Anomalies"])
async def get_top_anomalies(
    limit: int = Query(3, ge=1, le=10),
    db: AsyncSession = Depends(get_db)
):
    """Retrieves top N highest anomaly score events detected by Isolation Forest."""
    query = select(AnomalyResult).order_by(AnomalyResult.anomaly_score.desc()).limit(limit)
    res = await db.execute(query)
    return list(res.scalars().all())
