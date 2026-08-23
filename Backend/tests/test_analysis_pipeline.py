import pytest
from app.analysis.pipeline import AnalysisPipeline
from app.models.suspicious_event import SuspiciousEvent
from app.schemas.suspicious_event import (
    PipelineExecutionReport,
)
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select


@pytest.mark.asyncio
async def test_full_analysis_pipeline_execution(db_session: AsyncSession):
    pipeline = AnalysisPipeline(db_session)
    report = await pipeline.execute_full_pipeline()

    assert isinstance(report, PipelineExecutionReport)
    assert report.status == "COMPLETED"
    assert report.total_events_processed == 9
    assert report.reconciled_count == 9
    assert report.suspicious_events_generated == 9
    assert len(report.top_suspicious_events) == 3

    # Query DB for s3-evt-302 (Charlie 14GB download)
    res = await db_session.execute(select(SuspiciousEvent).where(SuspiciousEvent.event_id == "s3-evt-302"))
    s3_evt = res.scalars().first()

    assert s3_evt is not None
    assert s3_evt.weight_exfiltration_suspected is True
    assert s3_evt.severity in ["CRITICAL", "HIGH"]
    assert s3_evt.risk_score >= 60.0
    assert len(s3_evt.evidence) >= 3
    assert len(s3_evt.investigation_timeline) >= 3


@pytest.mark.asyncio
async def test_suspicious_events_rest_endpoints(client: AsyncClient, db_session: AsyncSession):
    # 1. Run complete pipeline via POST /api/v1/analysis/run
    run_resp = await client.post("/api/v1/analysis/run")
    assert run_resp.status_code == 200
    run_data = run_resp.json()
    assert run_data["status"] == "COMPLETED"
    assert run_data["total_events_processed"] == 9

    # 2. GET /api/v1/suspicious-events
    list_resp = await client.get("/api/v1/suspicious-events")
    assert list_resp.status_code == 200
    list_data = list_resp.json()
    assert len(list_data) == 9

    # 3. GET /api/v1/suspicious-events with user_id filter
    usr_resp = await client.get("/api/v1/suspicious-events?user_id=usr-003")
    assert usr_resp.status_code == 200
    usr_data = usr_resp.json()
    assert len(usr_data) >= 4

    # 4. GET /api/v1/suspicious-events with exfiltration filter
    exfil_resp = await client.get("/api/v1/suspicious-events?exfiltration_suspected=true")
    assert exfil_resp.status_code == 200
    exfil_data = exfil_resp.json()
    assert len(exfil_data) >= 1
    assert exfil_data[0]["event_id"] == "s3-evt-302"

    # 5. GET /api/v1/suspicious-events/top (must return exactly 3 events)
    top_resp = await client.get("/api/v1/suspicious-events/top")
    assert top_resp.status_code == 200
    top_data = top_resp.json()
    assert len(top_data) == 3
    assert top_data[0]["risk_score"] >= top_data[1]["risk_score"]
    assert top_data[1]["risk_score"] >= top_data[2]["risk_score"]

    # 6. GET /api/v1/dashboard/top-suspicious (must return top 3 events)
    dash_resp = await client.get("/api/v1/dashboard/top-suspicious")
    assert dash_resp.status_code == 200
    dash_data = dash_resp.json()
    assert len(dash_data) == 3

    # 7. GET /api/v1/suspicious-events/s3-evt-302 (single detail endpoint)
    detail_resp = await client.get("/api/v1/suspicious-events/s3-evt-302")
    assert detail_resp.status_code == 200
    detail_data = detail_resp.json()
    assert detail_data["event_id"] == "s3-evt-302"
    assert detail_data["weight_exfiltration_suspected"] is True
    assert len(detail_data["evidence"]) >= 3
    assert len(detail_data["investigation_timeline"]) >= 3
