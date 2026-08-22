import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.ingestion.service import IngestionService
from app.ml.feature_engineering import FeatureEngineeringPipeline
from app.ml.training import run_training_pipeline
from app.ml.model_manager import model_manager
from app.models import AnomalyResult


@pytest.mark.asyncio
async def test_feature_engineering_pipeline(db_session: AsyncSession):
    ingest = IngestionService()
    await ingest.run(db_session)

    pipeline = FeatureEngineeringPipeline()
    events = [
        {
            "event_id": "iam-evt-101",
            "source": "IAM",
            "event_time_raw": "2026-08-20T10:00:12Z",
            "user_id": "usr-001",
            "user_name": "arn:aws:iam::123456789012:user/alice.security",
            "ip_address": "192.168.1.50",
            "event_name": "ConsoleLogin",
            "bytes_transferred": 0
        },
        {
            "event_id": "s3-evt-302",
            "source": "S3",
            "event_time_raw": "2026-08-20T10:20:15Z",
            "user_id": "usr-003",
            "user_name": "arn:aws:iam::123456789012:user/charlie.compromised",
            "ip_address": "198.51.100.42",
            "event_name": "GetObject",
            "model_id": "mdl-llm-01",
            "bytes_transferred": 14000000000,
            "extra": {"key": "llm-cyber-v1.bin"}
        }
    ]

    X_df = pipeline.extract_features(events)
    assert X_df.shape[0] == 2
    assert X_df.shape[1] == len(pipeline.feature_names)
    assert X_df["is_large_transfer"].iloc[1] == 1.0
    assert X_df["is_large_transfer"].iloc[0] == 0.0

    X_scaled = pipeline.fit_transform(events)
    assert X_scaled.shape == (2, len(pipeline.feature_names))


@pytest.mark.asyncio
async def test_training_pipeline_and_detection(db_session: AsyncSession):
    ingest = IngestionService()
    await ingest.run(db_session)

    stats = await run_training_pipeline(db_session)
    assert stats["total_events"] == 9
    assert "flagged_anomalous_count" in stats
    assert "anomaly_score_distribution" in stats
    assert stats["training_time_ms"] > 0


@pytest.mark.asyncio
async def test_ml_api_endpoints(client: AsyncClient, db_session: AsyncSession):
    ingest = IngestionService()
    await ingest.run(db_session)

    # Train API endpoint
    train_resp = await client.post("/api/v1/ml/train", json={"contamination": 0.33, "model_version": "v1.0.0"})
    assert train_resp.status_code == 200
    train_data = train_resp.json()
    assert train_data["status"] == "SUCCESS"
    assert train_data["total_events"] == 9

    # Detect API endpoint
    detect_resp = await client.post("/api/v1/ml/detect")
    assert detect_resp.status_code == 200
    detect_data = detect_resp.json()
    assert detect_data["status"] == "COMPLETED"
    assert detect_data["total_events_evaluated"] == 9
    assert len(detect_data["results"]) == 9

    # Results API endpoint
    results_resp = await client.get("/api/v1/ml/results")
    assert results_resp.status_code == 200
    results_data = results_resp.json()
    assert len(results_data) == 9

    # Top anomalous results API endpoint
    top_resp = await client.get("/api/v1/ml/results/top?limit=3")
    assert top_resp.status_code == 200
    top_data = top_resp.json()
    assert len(top_data) == 3
    assert top_data[0]["anomaly_score"] >= top_data[1]["anomaly_score"]
