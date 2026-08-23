
from app.core.database import get_db
from app.models import (
    AnomalyResult,
    MLModel,
    NormalizedEvent,
    SuspiciousEvent,
    User,
)
from app.schemas.dashboard import DashboardSummaryResponse
from app.schemas.suspicious_event import SuspiciousEventResponse
from fastapi import APIRouter, Depends
from sqlalchemy import func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

router = APIRouter()


@router.get("/summary", response_model=DashboardSummaryResponse, tags=["Dashboard"])
async def get_dashboard_summary(db: AsyncSession = Depends(get_db)):
    """Retrieves high-level summary metrics and top 3 suspicious events for executive and analyst dashboards."""

    # 1. Total Models
    models_count_res = await db.execute(select(func.count(MLModel.model_id)))
    total_models = models_count_res.scalar() or 0

    # 2. Total Users
    users_count_res = await db.execute(select(func.count(User.user_id)))
    total_users = users_count_res.scalar() or 0

    # 3. Total Events
    events_count_res = await db.execute(select(func.count(NormalizedEvent.event_id)))
    total_events = events_count_res.scalar() or 0

    # 4. Anomalous Events
    anom_count_res = await db.execute(select(func.count(AnomalyResult.id)).where(AnomalyResult.is_anomaly == True))
    anomalous_events = anom_count_res.scalar() or 0
    if anomalous_events == 0:
        anom_flag_res = await db.execute(select(func.count(NormalizedEvent.event_id)).where(NormalizedEvent.anomaly_flag == True))
        anomalous_events = anom_flag_res.scalar() or 0

    # 5. Suspicious Events
    susp_count_res = await db.execute(select(func.count(SuspiciousEvent.id)))
    suspicious_events = susp_count_res.scalar() or 0

    # 6. Critical Events
    crit_count_res = await db.execute(select(func.count(SuspiciousEvent.id)).where(SuspiciousEvent.severity == "CRITICAL"))
    critical_events = crit_count_res.scalar() or 0

    # 7. Models at Risk
    models_risk_res = await db.execute(
        select(func.count(func.distinct(SuspiciousEvent.model_id))).where(
            SuspiciousEvent.severity.in_(["CRITICAL", "HIGH"]),
            SuspiciousEvent.model_id.isnot(None)
        )
    )
    models_at_risk = models_risk_res.scalar() or 0

    # 8. Exfiltration Suspected Events
    exfil_count_res = await db.execute(select(func.count(SuspiciousEvent.id)).where(SuspiciousEvent.weight_exfiltration_suspected == True))
    exfiltration_suspected_events = exfil_count_res.scalar() or 0

    # 9. Production Usage Events
    prod_count_res = await db.execute(select(func.count(NormalizedEvent.event_id)).where(NormalizedEvent.source == "MODEL"))
    production_usage_events = prod_count_res.scalar() or 0

    # 10. Top 3 Suspicious Events
    top_events_res = await db.execute(select(SuspiciousEvent).order_by(SuspiciousEvent.risk_score.desc()).limit(3))
    top_suspicious_events = list(top_events_res.scalars().all())

    return DashboardSummaryResponse(
        total_models=total_models,
        total_users=total_users,
        total_events=total_events,
        anomalous_events=anomalous_events,
        suspicious_events=suspicious_events,
        critical_events=critical_events,
        models_at_risk=models_at_risk,
        exfiltration_suspected_events=exfiltration_suspected_events,
        production_usage_events=production_usage_events,
        top_suspicious_events=[SuspiciousEventResponse.model_validate(e) for e in top_suspicious_events]
    )


@router.get("/top-suspicious", response_model=list[SuspiciousEventResponse], tags=["Dashboard"])
async def get_dashboard_top_suspicious(db: AsyncSession = Depends(get_db)):
    """Retrieves top 3 highest risk suspicious events for executive and analyst security dashboards."""
    res = await db.execute(select(SuspiciousEvent).order_by(SuspiciousEvent.risk_score.desc()).limit(3))
    return list(res.scalars().all())
