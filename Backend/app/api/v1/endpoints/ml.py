import time

from app.core.database import get_db
from app.core.logging import logger
from app.ml.model_manager import model_manager
from app.ml.training import run_training_pipeline
from app.models import AnomalyResult, DataLineage, MLModel, NormalizedEvent, User
from app.schemas.ml import (
    AnomalyResultResponse,
    DetectionReportResponse,
    TrainRequest,
    TrainResponse,
)
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

router = APIRouter()


@router.post("/train", response_model=TrainResponse, status_code=200, tags=["ML Anomaly Detection"])
async def train_model(
    req: TrainRequest = TrainRequest(),
    db: AsyncSession = Depends(get_db)
):
    """Triggers unsupervised IsolationForest training pipeline on normalized events."""
    try:
        stats = await run_training_pipeline(
            db=db,
            model_version=req.model_version,
            contamination=req.contamination
        )
        return TrainResponse(
            status="SUCCESS",
            model_version=req.model_version,
            training_time_ms=stats["training_time_ms"],
            total_events=stats["total_events"],
            flagged_anomalous_count=stats["flagged_anomalous_count"],
            threshold=stats["threshold"],
            anomaly_score_distribution=stats["anomaly_score_distribution"]
        )
    except Exception as e:
        logger.error(f"ML Training failed: {e}")
        raise HTTPException(status_code=500, detail=f"Training pipeline error: {e!s}")


@router.post("/detect", response_model=DetectionReportResponse, status_code=200, tags=["ML Anomaly Detection"])
async def run_detection(db: AsyncSession = Depends(get_db)):
    """Runs anomaly detection using the persisted IsolationForest model artifact and stores results in DB."""
    start_time = time.time()
    try:
        detector, pipeline, artifact = model_manager.load_model()
    except FileNotFoundError:
        # If no trained model exists, run training first
        await run_training_pipeline(db)
        detector, pipeline, artifact = model_manager.load_model()

    events_res = await db.execute(select(NormalizedEvent))
    events_models = events_res.scalars().all()

    events_data = [
        {
            "event_id": e.event_id,
            "source": e.source,
            "event_time_raw": e.event_time_raw,
            "user_id": e.user_id,
            "user_name": e.user_name,
            "ip_address": e.ip_address,
            "event_name": e.event_name,
            "model_id": e.model_id,
            "bytes_transferred": e.bytes_transferred,
            "extra": e.extra
        }
        for e in events_models
    ]

    models_res = await db.execute(select(MLModel))
    models_data = [{"model_id": m.model_id, "sensitivity_level": m.sensitivity_level} for m in models_res.scalars().all()]

    users_res = await db.execute(select(User))
    users_data = [{"user_id": u.user_id, "username": u.username, "role": u.role} for u in users_res.scalars().all()]

    X_scaled = pipeline.transform(events_data, models_data, users_data)
    scores, anomalies = detector.predict_anomalies(X_scaled)
    X_df = pipeline.extract_features(events_data, models_data, users_data)

    results = []
    anomalies_count = 0

    for idx, event_obj in enumerate(events_models):
        score = float(scores[idx])
        is_anom = bool(anomalies[idx])
        if is_anom:
            anomalies_count += 1

        feature_dict = X_df.iloc[idx].to_dict() if not X_df.empty else {}

        # Update or create AnomalyResult in DB
        existing_res = await db.execute(select(AnomalyResult).where(AnomalyResult.event_id == event_obj.event_id))
        existing = existing_res.scalars().first()

        if not existing:
            anom_res = AnomalyResult(
                event_id=event_obj.event_id,
                user_id=event_obj.user_id,
                model_id=event_obj.model_id,
                source=event_obj.source,
                anomaly_score=score,
                is_anomaly=is_anom,
                feature_values=feature_dict,
                model_version=artifact.get("model_version", "v1.0.0")
            )
            db.add(anom_res)
        else:
            existing.anomaly_score = score
            existing.is_anomaly = is_anom
            existing.feature_values = feature_dict
            existing.model_version = artifact.get("model_version", "v1.0.0")

        # Record Data Lineage
        lineage = DataLineage(
            event_id=event_obj.event_id,
            stage="ANOMALY_DETECTION",
            source_file="isolation_forest",
            status="COMPLETED",
            details={"score": score, "is_anomaly": is_anom}
        )
        db.add(lineage)

        results.append(
            AnomalyResultResponse(
                event_id=event_obj.event_id,
                user_id=event_obj.user_id,
                model_id=event_obj.model_id,
                source=event_obj.source,
                anomaly_score=score,
                is_anomaly=is_anom,
                feature_values=feature_dict,
                model_version=artifact.get("model_version", "v1.0.0"),
                detected_at=event_obj.event_time_raw
            )
        )

    await db.commit()
    detection_time_ms = round((time.time() - start_time) * 1000, 2)

    return DetectionReportResponse(
        status="COMPLETED",
        detection_time_ms=detection_time_ms,
        total_events_evaluated=len(events_models),
        anomalies_detected_count=anomalies_count,
        results=results
    )


@router.get("/results", response_model=list[AnomalyResultResponse], tags=["ML Anomaly Detection"])
async def get_anomaly_results(
    skip: int = 0,
    limit: int = 100,
    anomalous_only: bool = False,
    db: AsyncSession = Depends(get_db)
):
    """Retrieves persisted anomaly detection results from PostgreSQL/SQLite."""
    query = select(AnomalyResult)
    if anomalous_only:
        query = query.where(AnomalyResult.is_anomaly == True)
    query = query.order_by(AnomalyResult.anomaly_score.desc()).offset(skip).limit(limit)
    res = await db.execute(query)
    return list(res.scalars().all())


@router.get("/results/top", response_model=list[AnomalyResultResponse], tags=["ML Anomaly Detection"])
async def get_top_anomalous_results(limit: int = 3, db: AsyncSession = Depends(get_db)):
    """Retrieves top N highest risk anomalous events (PRD item 8 requirement)."""
    query = select(AnomalyResult).order_by(AnomalyResult.anomaly_score.desc()).limit(limit)
    res = await db.execute(query)
    return list(res.scalars().all())
