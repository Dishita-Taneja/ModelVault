import datetime
import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.ingestion.service import IngestionService
from app.models.reconciliation import ReconciliationResult
from app.reconciliation.engine import ReconciliationEngine, normalize_timestamp_to_utc
from app.reconciliation.config import ReconciliationConfig
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
    assert s3_rec.reconciliation_method in ["CROSS_SOURCE_TRIANGULATION", "DUAL_LOG_CORRELATION"]
    assert len(s3_rec.source_events_used) >= 2
    assert "ModelVault normalized timestamps to UTC" in s3_rec.reason_for_change


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


def test_normalize_timestamp_to_utc_valid():
    # Naive string
    dt_utc, valid, note = normalize_timestamp_to_utc("2026-08-22 14:30:00")
    assert valid is True
    assert dt_utc.tzinfo == datetime.timezone.utc
    assert dt_utc.year == 2026
    assert dt_utc.hour == 14

    # Aware string with offset +05:30
    dt_utc2, valid2, note2 = normalize_timestamp_to_utc("2026-08-22 14:30:00+05:30")
    assert valid2 is True
    assert dt_utc2.tzinfo == datetime.timezone.utc
    assert dt_utc2.hour == 9  # 14:30 +05:30 is 09:00 UTC


def test_normalize_timestamp_to_utc_missing_and_malformed():
    # Missing timestamp (None)
    dt_none, valid_none, note_none = normalize_timestamp_to_utc(None)
    assert valid_none is False
    assert note_none == "MISSING_TIMESTAMP"

    # Malformed timestamp string
    dt_bad, valid_bad, note_bad = normalize_timestamp_to_utc("not-a-valid-timestamp-12345")
    assert valid_bad is False
    assert note_bad == "MALFORMED_TIMESTAMP"


def test_reconciliation_identical_timestamps():
    engine = ReconciliationEngine()
    now_utc = datetime.datetime.now(datetime.timezone.utc)

    evt = {
        "event_id": "evt-1",
        "source": "IAM",
        "user_id": "usr-001",
        "ip_address": "192.168.1.50",
        "event_time_raw": now_utc,
        "event_time_reconciled": now_utc
    }
    result = engine.reconcile_single_event(evt, [evt])

    assert result["event_id"] == "evt-1"
    assert result["timestamp_offset_seconds"] == 0.0
    assert result["event_time_raw"] == now_utc
    assert result["confidence_score"] >= 0.85


def test_reconciliation_small_timestamp_offsets():
    engine = ReconciliationEngine()
    base_time = datetime.datetime(2026, 8, 22, 14, 0, 0, tzinfo=datetime.timezone.utc)
    reconciled_time = base_time + datetime.timedelta(seconds=15)

    evt = {
        "event_id": "evt-skew",
        "source": "EC2",
        "user_id": "usr-001",
        "ip_address": "10.0.0.1",
        "event_time_raw": base_time,
        "event_time_reconciled": reconciled_time
    }
    cand = {
        "event_id": "evt-anchor",
        "source": "IAM",
        "user_id": "usr-001",
        "ip_address": "10.0.0.1",
        "event_time_raw": base_time,
        "event_time_reconciled": base_time
    }

    result = engine.reconcile_single_event(evt, [evt, cand])
    assert result["timestamp_offset_seconds"] == 15.0
    assert result["confidence_score"] >= 0.90
    assert result["event_time_raw"] == base_time


def test_reconciliation_different_log_sources():
    engine = ReconciliationEngine()
    base_time = datetime.datetime(2026, 8, 22, 14, 0, 0, tzinfo=datetime.timezone.utc)

    iam_evt = {"event_id": "e1", "source": "IAM", "user_id": "u1", "ip_address": "1.1.1.1", "event_time_raw": base_time}
    ec2_evt = {"event_id": "e2", "source": "EC2", "user_id": "u1", "ip_address": "1.1.1.1", "event_time_raw": base_time + datetime.timedelta(seconds=2)}
    s3_evt = {"event_id": "e3", "source": "S3", "user_id": "u1", "ip_address": "1.1.1.1", "event_time_raw": base_time + datetime.timedelta(seconds=5)}

    result = engine.reconcile_single_event(s3_evt, [iam_evt, ec2_evt, s3_evt])

    assert result["reconciliation_method"] == "CROSS_SOURCE_TRIANGULATION"
    assert result["confidence_score"] == 1.0
    assert len(result["source_events_used"]) == 3


def test_reconciliation_events_outside_temporal_window():
    cfg = ReconciliationConfig(correlation_window_seconds=60.0)  # 60s window
    engine = ReconciliationEngine(config=cfg)

    t1 = datetime.datetime(2026, 8, 22, 10, 0, 0, tzinfo=datetime.timezone.utc)
    t2 = datetime.datetime(2026, 8, 22, 10, 15, 0, tzinfo=datetime.timezone.utc)  # 15 mins later

    evt1 = {"event_id": "e1", "source": "IAM", "user_id": "u1", "event_time_raw": t1}
    evt2 = {"event_id": "e2", "source": "S3", "user_id": "u1", "event_time_raw": t2}

    res1 = engine.reconcile_single_event(evt1, [evt1, evt2])
    res2 = engine.reconcile_single_event(evt2, [evt1, evt2])

    assert res1["reconciliation_method"] == "OUTSIDE_WINDOW_STANDALONE"
    assert res2["reconciliation_method"] == "OUTSIDE_WINDOW_STANDALONE"
    assert res1["confidence_score"] == 0.85
    assert res2["confidence_score"] == 0.85


def test_reconciliation_duplicate_events():
    engine = ReconciliationEngine()
    now_utc = datetime.datetime.now(datetime.timezone.utc)

    evt1 = {"event_id": "e-dup", "source": "IAM", "user_id": "u1", "event_time_raw": now_utc}
    evt2 = {"event_id": "e-dup", "source": "IAM", "user_id": "u1", "event_time_raw": now_utc}

    res = engine.reconcile_single_event(evt1, [evt1, evt2])
    assert len(res["source_events_used"]) == 1
