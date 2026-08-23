import pytest
from app.correlation.engine import CrossSourceCorrelationEngine
from app.ingestion.service import IngestionService
from app.ml.training import run_training_pipeline
from app.reconciliation.engine import ReconciliationEngine
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession


@pytest.mark.asyncio
async def test_correlate_by_user(db_session: AsyncSession):
    # Ingest data
    ingest = IngestionService()
    await ingest.run(db_session)
    
    # Run reconciliation & ML detection
    rec = ReconciliationEngine(db_session)
    await rec.reconcile_all()
    await run_training_pipeline(db_session)

    # Correlate for Charlie (usr-003)
    corr_engine = CrossSourceCorrelationEngine(db_session)
    timeline_resp = await corr_engine.correlate_by_user("usr-003")

    assert timeline_resp.target_type == "USER"
    assert timeline_resp.target_id == "usr-003"
    assert timeline_resp.total_events_count == 5
    assert len(timeline_resp.timeline) == 5

    # Check chronological ordering
    timestamps = [t.timestamp for t in timeline_resp.timeline]
    assert sorted(timestamps) == timestamps

    # Verify event composition: IAM -> IAM -> EC2 -> S3 -> MODEL
    sources = [t.source for t in timeline_resp.timeline]
    assert sources == ["IAM", "IAM", "EC2", "S3", "MODEL"]

    # Check incident severity
    assert timeline_resp.severity in ["HIGH", "CRITICAL"]


@pytest.mark.asyncio
async def test_correlate_by_model(db_session: AsyncSession):
    ingest = IngestionService()
    await ingest.run(db_session)

    corr_engine = CrossSourceCorrelationEngine(db_session)
    timeline_resp = await corr_engine.correlate_by_model("mdl-llm-01")

    assert timeline_resp.target_type == "MODEL"
    assert timeline_resp.target_id == "mdl-llm-01"
    assert timeline_resp.total_events_count >= 2

    # Verify 14GB weight transfer event present
    exfil_evt = next((t for t in timeline_resp.timeline if t.event_id == "s3-evt-302"), None)
    assert exfil_evt is not None
    assert exfil_evt.evidence["bytes_transferred"] == 14000000000


@pytest.mark.asyncio
async def test_investigation_api_endpoints(client: AsyncClient, db_session: AsyncSession):
    ingest = IngestionService()
    await ingest.run(db_session)

    # GET /api/v1/investigations/user/usr-003
    usr_resp = await client.get("/api/v1/investigations/user/usr-003")
    assert usr_resp.status_code == 200
    usr_data = usr_resp.json()
    assert usr_data["target_id"] == "usr-003"
    assert len(usr_data["timeline"]) == 5

    # GET /api/v1/investigations/model/mdl-llm-01
    mdl_resp = await client.get("/api/v1/investigations/model/mdl-llm-01")
    assert mdl_resp.status_code == 200
    mdl_data = mdl_resp.json()
    assert mdl_data["target_id"] == "mdl-llm-01"

    # GET /api/v1/investigations/event/s3-evt-302
    evt_resp = await client.get("/api/v1/investigations/event/s3-evt-302")
    assert evt_resp.status_code == 200
    evt_data = evt_resp.json()
    assert evt_data["target_id"] == "s3-evt-302"
    assert len(evt_data["timeline"]) >= 1
