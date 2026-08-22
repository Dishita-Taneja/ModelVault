from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.models.event import NormalizedEvent
from app.schemas.event import NormalizedEventCreate


async def get_event_by_id(db: AsyncSession, event_id: str) -> Optional[NormalizedEvent]:
    result = await db.execute(select(NormalizedEvent).where(NormalizedEvent.event_id == event_id))
    return result.scalars().first()


async def get_all_events(
    db: AsyncSession,
    skip: int = 0,
    limit: int = 100,
    anomalous_only: bool = False
) -> List[NormalizedEvent]:
    query = select(NormalizedEvent)
    if anomalous_only:
        query = query.where(NormalizedEvent.anomaly_flag == True)
    query = query.order_by(NormalizedEvent.reconciled_timestamp.desc()).offset(skip).limit(limit)
    result = await db.execute(query)
    return list(result.scalars().all())


async def create_event(db: AsyncSession, event_in: NormalizedEventCreate) -> NormalizedEvent:
    db_event = NormalizedEvent(
        event_id=event_in.event_id,
        timestamp=event_in.timestamp,
        reconciled_timestamp=event_in.reconciled_timestamp,
        log_source=event_in.log_source,
        user_id=event_in.user_id,
        user_arn=event_in.user_arn,
        source_ip=event_in.source_ip,
        resource_arn=event_in.resource_arn,
        model_id=event_in.model_id,
        action=event_in.action,
        status=event_in.status,
        bytes_transferred=event_in.bytes_transferred,
        risk_score=event_in.risk_score,
        anomaly_flag=event_in.anomaly_flag
    )
    db.add(db_event)
    await db.commit()
    await db.refresh(db_event)
    return db_event
