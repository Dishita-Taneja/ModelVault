import uuid
from collections.abc import Sequence
from datetime import datetime
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.anomaly_result import AnomalyResult
from app.models.access_event import AccessEvent
from app.schemas.anomaly_result import AnomalyResultCreate


async def get_anomaly_results(
    db: AsyncSession,
    user_id: uuid.UUID | None = None,
    model_id: uuid.UUID | None = None,
    start_time: datetime | None = None,
    end_time: datetime | None = None,
    skip: int = 0,
    limit: int = 100,
) -> Sequence[AnomalyResult]:
    stmt = select(AnomalyResult)

    if user_id is not None or model_id is not None or start_time is not None or end_time is not None:
        stmt = stmt.join(AccessEvent, AnomalyResult.access_event_id == AccessEvent.id)
        if user_id is not None:
            stmt = stmt.where(AccessEvent.user_id == user_id)
        if model_id is not None:
            stmt = stmt.where(AccessEvent.model_id == model_id)
        if start_time is not None:
            stmt = stmt.where(AccessEvent.timestamp >= start_time)
        if end_time is not None:
            stmt = stmt.where(AccessEvent.timestamp <= end_time)

    stmt = stmt.offset(skip).limit(limit).order_by(AnomalyResult.flagged_at.desc())
    result = await db.execute(stmt)
    return result.scalars().all()


async def get_anomaly_result_by_id(
    db: AsyncSession,
    result_id: uuid.UUID,
) -> AnomalyResult | None:
    stmt = select(AnomalyResult).where(AnomalyResult.id == result_id)
    result = await db.execute(stmt)
    return result.scalar_one_or_none()


async def create_anomaly_result(
    db: AsyncSession,
    result_in: AnomalyResultCreate,
) -> AnomalyResult:
    anomaly = AnomalyResult(
        access_event_id=result_in.access_event_id,
        anomaly_score=result_in.anomaly_score,
        reason=result_in.reason,
        flagged_at=result_in.flagged_at,
    )
    db.add(anomaly)
    await db.flush()
    await db.refresh(anomaly)
    return anomaly
