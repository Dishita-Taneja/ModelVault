import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.ingestion.service import IngestionService
from app.reconciliation.engine import ReconciliationEngine
from app.models.reconciliation import ReconciliationResult
from app.schemas.reconciliation import ReconciliationRunReport


@pytest.mark.asyncio
async def test_reconciliation_engine_execution(db_session: AsyncSession):
    # Ingest data
    ingest_service = IngestionService()
    await ingest_service.run(db_session)

    # Run reconciliation engine
    rec_engine = ReconciliationEngine(db_session)
    report = await rec_engine.reconcile_all()

    assert isinstance(report, ReconciliationRunReport)
    assert report.total_events_reconciled == 9
    assert report.high_confidence_count == 9

    # Query DB results
    res = await db_session.execute(select(ReconciliationResult))
    reconciliations = list(res.scalars().all())
    assert len(reconciliations) == 9

    # Check S3 event reconciliation audit trail
    s3_rec = next((r for r in reconciliations if r.event_id == "s3-evt-302"), None)
    assert s3_rec is not None
    assert s3_rec.confidence_score >= 0.95
    assert s3_rec.reconciliation_method == "CROSS_SOURCE_TRIANGULATION"
    assert len(s3_rec.source_events_used) >= 3
    assert "charlie.compromised" in s3_rec.reason_for_change


@pytest.mark.asyncio
async def test_reconciliation_api_endpoints(client: AsyncClient, db_session: AsyncSession):
    # Ingest data first
    ingest_service = IngestionService()
    await ingest_service.run(db_session)

    # Run reconciliation API endpoint
    run_resp = await client.post("/api/v1/reconciliation/run")
    assert run_resp.status_code == 200
    run_data = run_resp.json()
    assert run_data["total_events_reconciled"] == 9

    # List reconciliations API endpoint
    list_resp = await client.get("/api/v1/reconciliation/")
    assert list_resp.status_code == 200
    list_data = list_resp.json()
    assert len(list_data) == 9

    # Get single reconciliation detail API endpoint
    detail_resp = await client.get("/api/v1/reconciliation/s3-evt-302")
    assert detail_resp.status_code == 200
    detail_data = detail_resp.json()
    assert detail_data["event_id"] == "s3-evt-302"
    assert detail_data["confidence_score"] >= 0.95
    assert len(detail_data["source_events_used"]) >= 3
