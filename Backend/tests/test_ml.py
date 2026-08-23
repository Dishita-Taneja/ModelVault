import os
import tempfile
from pathlib import Path
import numpy as np
import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.ingestion.service import IngestionService
from app.ml.anomaly_detector import AnomalyDetector
from app.ml.feature_engineering import FeatureEngineeringPipeline
from app.ml.model_manager import ModelManager
from app.ml.training import run_training_pipeline


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
    assert stats["threshold"] >= 0.40
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


def test_normal_vs_suspicious_behavior_scores():
    pipeline = FeatureEngineeringPipeline()

    normal_events = [
        {"event_id": f"n-{i}", "source": "IAM", "event_time_raw": "2026-08-22T10:00:00Z", "user_id": "u1", "ip_address": "192.168.1.1", "bytes_transferred": 0, "event_name": "GetRole"}
        for i in range(10)
    ]
    suspicious_event = {
        "event_id": "s-1",
        "source": "S3",
        "event_time_raw": "2026-08-22T03:00:00Z",  # off-hours
        "user_id": "u2",
        "ip_address": "198.51.100.99",
        "bytes_transferred": 15000000000,  # 15 GB
        "event_name": "GetObject",
        "extra": {"key": "weights.bin"}
    }

    all_events = normal_events + [suspicious_event]
    X_scaled = pipeline.fit_transform(all_events)

    detector = AnomalyDetector(contamination=0.10, random_state=42)
    detector.fit(X_scaled)

    scores, anomalies = detector.predict_anomalies(X_scaled)
    
    normal_max_score = float(np.max(scores[:-1]))
    suspicious_score = float(scores[-1])

    assert suspicious_score > normal_max_score
    assert anomalies[-1] is np.bool_(True) or anomalies[-1] == True


def test_deterministic_threshold_behavior():
    np.random.seed(42)
    X = np.random.randn(50, 10)
    
    # Add outlier cluster
    X[-5:] += 10.0

    detector1 = AnomalyDetector(contamination=0.10, random_state=42)
    detector1.fit(X)
    s1, a1 = detector1.predict_anomalies(X)

    detector2 = AnomalyDetector(contamination=0.10, random_state=42)
    detector2.fit(X)
    s2, a2 = detector2.predict_anomalies(X)

    assert detector1.threshold_norm == detector2.threshold_norm
    np.testing.assert_array_almost_equal(s1, s2)
    np.testing.assert_array_equal(a1, a2)


def test_persisted_model_inference():
    pipeline = FeatureEngineeringPipeline()
    events = [
        {"event_id": "e1", "source": "IAM", "event_time_raw": "2026-08-22T10:00:00Z", "user_id": "u1", "bytes_transferred": 0},
        {"event_id": "e2", "source": "S3", "event_time_raw": "2026-08-22T02:00:00Z", "user_id": "u2", "bytes_transferred": 20000000000, "extra": {"key": "model.pt"}}
    ]
    X_scaled = pipeline.fit_transform(events)

    detector = AnomalyDetector(contamination=0.50, random_state=42)
    detector.fit(X_scaled)
    s_orig, a_orig = detector.predict_anomalies(X_scaled)

    with tempfile.TemporaryDirectory() as tmpdir:
        mm = ModelManager(artifacts_dir=Path(tmpdir))
        target_file = Path(tmpdir) / "test_model.joblib"
        mm.save_model(detector, pipeline, model_version="v_test", file_path=target_file)

        loaded_detector, loaded_pipeline, _ = mm.load_model(file_path=target_file)
        X_loaded = loaded_pipeline.transform(events)
        s_loaded, a_loaded = loaded_detector.predict_anomalies(X_loaded)

        np.testing.assert_array_almost_equal(s_orig, s_loaded)
        np.testing.assert_array_equal(a_orig, a_loaded)


def test_missing_and_invalid_feature_values_handling():
    pipeline = FeatureEngineeringPipeline()

    malformed_events = [
        {},
        {"bytes_transferred": None, "event_time_raw": "invalid-timestamp-string"},
        {"source": None, "extra": "not-a-dict", "model_id": None}
    ]

    X_df = pipeline.extract_features(malformed_events)
    assert X_df.shape[0] == 3
    assert X_df.shape[1] == len(pipeline.feature_names)
    assert not X_df.isnull().values.any()
