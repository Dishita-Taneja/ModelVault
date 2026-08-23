import time
from typing import Any

import numpy as np
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.core.logging import logger
from app.ml.anomaly_detector import AnomalyDetector
from app.ml.feature_engineering import FeatureEngineeringPipeline
from app.ml.model_manager import model_manager
from app.models import DataLineage, MLModel, NormalizedEvent, User


async def run_training_pipeline(
    db: AsyncSession,
    model_version: str = "v1.0.0",
    contamination: float = 0.33
) -> dict[str, Any]:
    start_time = time.time()
    logger.info("Starting ML Training Pipeline...")

    # 1. Fetch data from DB
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

    if not events_data:
        raise ValueError("No normalized events found in database. Ingest dataset before training ML model.")

    # 2. Feature Engineering & Preprocessing
    pipeline = FeatureEngineeringPipeline()
    X_scaled = pipeline.fit_transform(events_data, models_data, users_data)

    # 3. Fit Isolation Forest Detector (Unsupervised)
    detector = AnomalyDetector(contamination=contamination, n_estimators=100, random_state=42)
    detector.fit(X_scaled)

    # 4. Predict anomaly scores on training set
    scores, anomalies = detector.predict_anomalies(X_scaled)

    # 5. Persist Trained Artifacts
    training_time_ms = round((time.time() - start_time) * 1000, 2)
    
    stats = {
        "total_events": len(events_data),
        "flagged_anomalous_count": int(np.sum(anomalies)),
        "anomaly_score_distribution": {
            "min": float(np.min(scores)),
            "max": float(np.max(scores)),
            "mean": float(np.mean(scores)),
            "std": float(np.std(scores)),
            "p50": float(np.percentile(scores, 50)),
            "p75": float(np.percentile(scores, 75)),
            "p90": float(np.percentile(scores, 90))
        },
        "threshold": float(detector.threshold_norm),
        "training_time_ms": training_time_ms
    }

    model_manager.save_model(detector, pipeline, model_version=model_version, training_stats=stats)

    # Record training lineage
    for e in events_models:
        lineage = DataLineage(
            event_id=e.event_id,
            stage="FEATURE_EXTRACTION",
            source_file="ml_pipeline",
            status="COMPLETED",
            details={"features_count": len(pipeline.feature_names)}
        )
        db.add(lineage)

    await db.commit()
    logger.info(f"Training pipeline completed in {training_time_ms}ms. Flagged {stats['flagged_anomalous_count']}/{stats['total_events']} anomalous events.")
    return stats
