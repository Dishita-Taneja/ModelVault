import uuid
from typing import Any
from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from app.core.database import get_db
from app.models.access_event import AccessEvent
from app.models.anomaly_result import AnomalyResult
from app.models.model import MLModel
from app.models.user import User

router = APIRouter(tags=["Dashboard & Telemetry"])


class ReviewPayload(BaseModel):
    reviewed: bool = True


@router.get("/dashboard/stats", summary="Get dashboard summary telemetry")
async def get_dashboard_stats(db: AsyncSession = Depends(get_db)) -> dict[str, int]:
    total_models = await db.scalar(select(func.count(MLModel.id))) or 0
    flagged_count = await db.scalar(select(func.count(func.distinct(AccessEvent.model_id))).join(AnomalyResult, AnomalyResult.access_event_id == AccessEvent.id)) or 0
    active_anomalies = await db.scalar(select(func.count(AnomalyResult.id)).where(AnomalyResult.reviewed == False)) or 0  # noqa: E712

    return {
        "total_models": total_models,
        "flagged_count": flagged_count,
        "active_anomalies": active_anomalies,
    }


@router.get("/dashboard/top-suspicious", summary="Get top 3 suspicious models with evidence")
async def get_dashboard_top_suspicious(db: AsyncSession = Depends(get_db)) -> list[dict[str, Any]]:
    stmt = (
        select(AnomalyResult)
        .options(
            joinedload(AnomalyResult.access_event).joinedload(AccessEvent.model),
            joinedload(AnomalyResult.access_event).joinedload(AccessEvent.user),
        )
        .order_by(AnomalyResult.anomaly_score.desc())
        .limit(3)
    )
    results = (await db.execute(stmt)).scalars().all()

    output = []
    for r in results:
        ev = r.access_event
        mod = ev.model if ev else None
        usr = ev.user if ev else None

        output.append({
            "model_id": str(mod.id) if mod else str(r.id),
            "model_name": mod.name if mod else "unknown-model",
            "owner": usr.username if usr else "system",
            "anomaly_score": r.anomaly_score,
            "reason": r.reason,
            "flagged_at": r.flagged_at.isoformat() if r.flagged_at else None,
            "reviewed": r.reviewed,
            "evidence": [
                {
                    "event_id": str(ev.id) if ev else str(r.access_event_id),
                    "source": ev.source if ev else "API_GATEWAY",
                    "event_name": ev.action if ev else "Access",
                    "event_time_reconciled": ev.timestamp.isoformat() if ev and ev.timestamp else None,
                    "ip_address": ev.raw_metadata.get("ip_address", "127.0.0.1") if ev and isinstance(ev.raw_metadata, dict) else "127.0.0.1",
                    "extra": ev.raw_metadata if ev else {},
                }
            ] if ev else [],
        })
    return output


@router.get("/dashboard/flagged-models", summary="List flagged models with filters")
async def get_dashboard_flagged_models(
    reviewed: bool | None = Query(None, description="Filter by reviewed status"),
    min_score: float | None = Query(None, description="Filter by minimum anomaly score"),
    user_id: str | None = Query(None, description="Filter by user handle or UUID"),
    model_id: str | None = Query(None, description="Filter by model name or UUID"),
    db: AsyncSession = Depends(get_db),
) -> list[dict[str, Any]]:
    stmt = (
        select(AnomalyResult)
        .options(
            joinedload(AnomalyResult.access_event).joinedload(AccessEvent.model),
            joinedload(AnomalyResult.access_event).joinedload(AccessEvent.user),
        )
        .order_by(AnomalyResult.anomaly_score.desc())
    )

    if reviewed is not None:
        stmt = stmt.where(AnomalyResult.reviewed == reviewed)
    if min_score is not None:
        stmt = stmt.where(AnomalyResult.anomaly_score >= min_score)

    results = (await db.execute(stmt)).scalars().all()

    output = []
    for r in results:
        ev = r.access_event
        mod = ev.model if ev else None
        usr = ev.user if ev else None

        if user_id and usr and usr.username != user_id and str(usr.id) != user_id:
            continue
        if model_id and mod and mod.name != model_id and str(mod.id) != model_id:
            continue

        output.append({
            "model_id": str(mod.id) if mod else str(r.id),
            "model_name": mod.name if mod else "unknown-model",
            "owner": usr.username if usr else "system",
            "anomaly_score": r.anomaly_score,
            "reason": r.reason,
            "flagged_at": r.flagged_at.isoformat() if r.flagged_at else None,
            "reviewed": r.reviewed,
            "evidence": [
                {
                    "event_id": str(ev.id) if ev else str(r.access_event_id),
                    "source": ev.source if ev else "API_GATEWAY",
                    "event_name": ev.action if ev else "Access",
                    "event_time_reconciled": ev.timestamp.isoformat() if ev and ev.timestamp else None,
                    "ip_address": ev.raw_metadata.get("ip_address", "127.0.0.1") if ev and isinstance(ev.raw_metadata, dict) else "127.0.0.1",
                    "extra": ev.raw_metadata if ev else {},
                }
            ] if ev else [],
        })
    return output


@router.get("/events", summary="List raw access events (alias)")
async def get_events_alias(
    user_id: uuid.UUID | None = Query(None),
    model_id: uuid.UUID | None = Query(None),
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
):
    stmt = select(AccessEvent).offset(offset).limit(limit).order_by(AccessEvent.timestamp.desc())
    if user_id:
        stmt = stmt.where(AccessEvent.user_id == user_id)
    if model_id:
        stmt = stmt.where(AccessEvent.model_id == model_id)
    events = (await db.execute(stmt)).scalars().all()
    return events


@router.get("/flagged-models/{model_id}/evidence", summary="Get evidence for a flagged model")
async def get_flagged_model_evidence(
    model_id: str,
    db: AsyncSession = Depends(get_db),
) -> list[dict[str, Any]]:
    # Try searching by model UUID
    try:
        m_uuid = uuid.UUID(model_id)
        stmt = select(AccessEvent).where(AccessEvent.model_id == m_uuid).order_by(AccessEvent.timestamp.desc())
        events = (await db.execute(stmt)).scalars().all()
    except ValueError:
        events = []

    return [
        {
            "event_id": str(e.id),
            "source": e.source,
            "event_name": e.action,
            "event_time_reconciled": e.timestamp.isoformat(),
            "ip_address": e.raw_metadata.get("ip_address", "127.0.0.1") if isinstance(e.raw_metadata, dict) else "127.0.0.1",
            "extra": e.raw_metadata,
        }
        for e in events
    ]


@router.patch("/flagged-models/{model_id}/review", summary="Toggle reviewed status of a model's anomalies")
async def review_flagged_model(
    model_id: str,
    payload: ReviewPayload,
    db: AsyncSession = Depends(get_db),
):
    try:
        m_uuid = uuid.UUID(model_id)
        # Find anomalies for events linked to this model
        stmt = (
            select(AnomalyResult)
            .join(AccessEvent, AnomalyResult.access_event_id == AccessEvent.id)
            .where(AccessEvent.model_id == m_uuid)
        )
        anomalies = (await db.execute(stmt)).scalars().all()
    except ValueError:
        anomalies = []

    if not anomalies:
        # Check by anomaly ID directly
        try:
            anom_uuid = uuid.UUID(model_id)
            stmt = select(AnomalyResult).where(AnomalyResult.id == anom_uuid)
            anomalies = (await db.execute(stmt)).scalars().all()
        except ValueError:
            pass

    for anom in anomalies:
        anom.reviewed = payload.reviewed

    await db.commit()
    return {"model_id": model_id, "reviewed": payload.reviewed, "updated_count": len(anomalies)}
