import uuid
from collections.abc import Sequence
from datetime import datetime
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.access_event import AccessEvent
from app.schemas.access_event import AccessEventCreate


async def get_access_events(
    db: AsyncSession,
    user_id: uuid.UUID | None = None,
    model_id: uuid.UUID | None = None,
    start_time: datetime | None = None,
    end_time: datetime | None = None,
    skip: int = 0,
    limit: int = 100,
) -> Sequence[AccessEvent]:
    stmt = select(AccessEvent)

    if user_id is not None:
        stmt = stmt.where(AccessEvent.user_id == user_id)
    if model_id is not None:
        stmt = stmt.where(AccessEvent.model_id == model_id)
    if start_time is not None:
        stmt = stmt.where(AccessEvent.timestamp >= start_time)
    if end_time is not None:
        stmt = stmt.where(AccessEvent.timestamp <= end_time)

    stmt = stmt.offset(skip).limit(limit).order_by(AccessEvent.timestamp.desc())
    result = await db.execute(stmt)
    return result.scalars().all()


async def get_access_event_by_id(
    db: AsyncSession,
    event_id: uuid.UUID,
) -> AccessEvent | None:
    stmt = select(AccessEvent).where(AccessEvent.id == event_id)
    result = await db.execute(stmt)
    return result.scalar_one_or_none()


async def create_access_event(
    db: AsyncSession,
    event_in: AccessEventCreate,
) -> AccessEvent:
    event = AccessEvent(
        user_id=event_in.user_id,
        model_id=event_in.model_id,
        action=event_in.action,
        timestamp=event_in.timestamp,
        source=event_in.source,
        raw_metadata=event_in.raw_metadata,
    )
    db.add(event)
    await db.flush()
    await db.refresh(event)
    return event
