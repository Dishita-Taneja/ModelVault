from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.models.alert import Alert
from app.schemas.alert import AlertCreate


async def get_alert_by_id(db: AsyncSession, alert_id: str) -> Optional[Alert]:
    result = await db.execute(select(Alert).where(Alert.alert_id == alert_id))
    return result.scalars().first()


async def get_top_suspicious_events(db: AsyncSession, limit: int = 3) -> List[Alert]:
    query = select(Alert).order_by(Alert.risk_score.desc()).limit(limit)
    result = await db.execute(query)
    return list(result.scalars().all())


async def create_alert(db: AsyncSession, alert_in: AlertCreate) -> Alert:
    db_alert = Alert(
        alert_id=alert_in.alert_id,
        event_id=alert_in.event_id,
        model_id=alert_in.model_id,
        user_arn=alert_in.user_arn,
        risk_score=alert_in.risk_score,
        severity=alert_in.severity,
        title=alert_in.title,
        description=alert_in.description,
        status=alert_in.status
    )
    db.add(db_alert)
    await db.commit()
    await db.refresh(db_alert)
    return db_alert
