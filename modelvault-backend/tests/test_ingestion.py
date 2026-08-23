import json
import tempfile
from pathlib import Path

import pytest
from app.ingestion.service import IngestionService
from app.models import DataLineage, MLModel, NormalizedEvent, RawLog, User
from app.schemas.event import IngestionReport
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select


@pytest.mark.asyncio
async def test_full_dataset_ingestion(db_session: AsyncSession):
    service = IngestionService()
    report = await service.run(db_session)

    assert isinstance(report, IngestionReport)
    assert report.total_files_processed == 7

    # Verify Record Counts
    users_res = await db_session.execute(select(User))
    users = users_res.scalars().all()
    assert len(users) == 3

    models_res = await db_session.execute(select(MLModel))
    models = models_res.scalars().all()
    assert len(models) == 3

    events_res = await db_session.execute(select(NormalizedEvent))
    events = events_res.scalars().all()
    assert len(events) == 9  # 3 IAM + 2 EC2 + 2 S3 + 2 MODEL events

    raw_res = await db_session.execute(select(RawLog))
    raw_logs = raw_res.scalars().all()
    assert len(raw_logs) == 9

    lineage_res = await db_session.execute(select(DataLineage))
    lineage = lineage_res.scalars().all()
    assert len(lineage) >= 27  # At least 3 lineage stages per event


@pytest.mark.asyncio
async def test_field_mapping_and_relationships(db_session: AsyncSession):
    service = IngestionService()
    await service.run(db_session)

    # Test S3 Log event field mapping & Model relationship
    s3_event_res = await db_session.execute(
        select(NormalizedEvent).where(NormalizedEvent.event_id == "s3-evt-302")
    )
    s3_event = s3_event_res.scalars().first()
    assert s3_event is not None
    assert s3_event.source == "S3"
    assert s3_event.bytes_transferred == 14000000000
    assert s3_event.user_id == "usr-003"
    assert s3_event.model_id == "mdl-llm-01"
    assert s3_event.user_name == "arn:aws:iam::123456789012:user/charlie.compromised"
    assert s3_event.ip_address == "198.51.100.42"
    assert "bucket" in s3_event.extra
    assert s3_event.extra["bucket"] == "modelvault-weights"

    # Test Model Access Log field mapping & Model relationship
    mdl_event_res = await db_session.execute(
        select(NormalizedEvent).where(NormalizedEvent.event_id == "mdl-evt-402")
    )
    mdl_event = mdl_event_res.scalars().first()
    assert mdl_event is not None
    assert mdl_event.source == "MODEL"
    assert mdl_event.model_id == "mdl-llm-01"
    assert mdl_event.user_id == "usr-003"
    assert mdl_event.extra["input_tokens"] == 8192


@pytest.mark.asyncio
async def test_idempotent_reingestion(db_session: AsyncSession):
    service = IngestionService()
    
    # Run 1
    report1 = await service.run(db_session)
    events_count1 = len((await db_session.execute(select(NormalizedEvent))).scalars().all())

    # Run 2 (Re-ingest)
    report2 = await service.run(db_session)
    events_count2 = len((await db_session.execute(select(NormalizedEvent))).scalars().all())

    # Verify no duplicate records created
    assert events_count1 == events_count2 == 9
    # Verify duplicates were skipped
    assert sum(report2.duplicates_skipped.values()) > 0


@pytest.mark.asyncio
async def test_invalid_record_handling(db_session: AsyncSession):
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_path = Path(tmpdir)
        
        # Create valid users file
        users_file = tmp_path / "users.json"
        users_file.write_text(json.dumps([
            {
                "user_id": "usr-999",
                "username": "test.user",
                "email": "invalid-email-format",  # Invalid Email
                "role": "Analyst",
                "created_at": "2026-01-01T00:00:00Z"
            }
        ]))

        # Create valid IAM logs with 1 valid and 1 invalid log
        iam_file = tmp_path / "iam_logs.json"
        iam_file.write_text(json.dumps([
            {
                "event_id": "iam-evt-valid",
                "timestamp": "2026-08-20T10:00:00Z",
                "user_arn": "arn:aws:iam::123456789012:user/test.user",
                "action": "ConsoleLogin",
                "status": "SUCCESS"
            },
            {
                # Missing required event_id & timestamp
                "action": "CorruptEvent"
            }
        ]))

        service = IngestionService(data_dir=tmp_path)
        report = await service.run(db_session)

        assert report.invalid_records["users.json"] == 1
        assert report.invalid_records["iam_logs.json"] == 1
        assert len(report.errors) == 2
