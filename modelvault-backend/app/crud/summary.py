from collections.abc import Sequence
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from app.models.anomaly_result import AnomalyResult


async def get_top_suspicious_events(
    db: AsyncSession,
    limit: int = 3,
) -> Sequence[AnomalyResult]:
    stmt = (
        select(AnomalyResult)
        .options(joinedload(AnomalyResult.access_event))
        .order_by(AnomalyResult.anomaly_score.desc())
        .limit(limit)
    )
    result = await db.execute(stmt)
    return result.scalars().all()
