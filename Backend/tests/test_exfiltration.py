import pytest
from app.exfiltration.detector import ExfiltrationDetector
from app.ingestion.service import IngestionService
from app.ml.training import run_training_pipeline
from app.reconciliation.engine import ReconciliationEngine
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession


@pytest.mark.asyncio
async def test_exfiltration_detection_suspicious_event(db_session: AsyncSession):
    # Ingest data & run prerequisites
    ingest = IngestionService()
    await ingest.run(db_session)
    rec = ReconciliationEngine(db_session)
    await rec.reconcile_all()
    await run_training_pipeline(db_session)

    detector = ExfiltrationDetector(db_session)
    resp = await detector.assess_event("s3-evt-302")

    assert resp.event_id == "s3-evt-302"
    assert resp.weight_exfiltration_suspected is True
    assert resp.confidence >= 0.90
    assert resp.risk_score >= 60.0
    assert len(resp.evidence) >= 3
    assert any("14,000,000,000 bytes" in e or "14.00 GB" in e for e in resp.evidence)
    assert any("CRITICAL" in e for e in resp.evidence)
    assert len(resp.related_events) >= 3


@pytest.mark.asyncio
async def test_exfiltration_detection_normal_events(db_session: AsyncSession):
    ingest = IngestionService()
    await ingest.run(db_session)
    rec = ReconciliationEngine(db_session)
    await rec.reconcile_all()
    await run_training_pipeline(db_session)

    detector = ExfiltrationDetector(db_session)

    # Legitimate S3 download (Bob)
    resp_s3_301 = await detector.assess_event("s3-evt-301")
    assert resp_s3_301.weight_exfiltration_suspected is False

    # Legitimate Model inference invocation
    resp_mdl_401 = await detector.assess_event("mdl-evt-401")
    assert resp_mdl_401.weight_exfiltration_suspected is False


@pytest.mark.asyncio
async def test_exfiltration_api_endpoint(client: AsyncClient, db_session: AsyncSession):
    ingest = IngestionService()
    await ingest.run(db_session)

    http_resp = await client.get("/api/v1/exfiltration/s3-evt-302")
    assert http_resp.status_code == 200
    data = http_resp.json()
    assert data["event_id"] == "s3-evt-302"
    assert data["weight_exfiltration_suspected"] is True
    assert data["confidence"] >= 0.90
    assert "llm-cyber-v1.bin" in data["reason"] or "14.00 GB" in data["reason"] or "exfiltration" in data["reason"]
