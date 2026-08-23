import datetime
import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import NormalizedEvent, SuspiciousEvent


@pytest.mark.asyncio
async def test_db_filtering_and_pagination(client: AsyncClient, db_session: AsyncSession):
    """
    Test SQL database query optimization for filtering, sorting, pagination, and empty results.
    """
    now = datetime.datetime.now(datetime.timezone.utc)

    # 1. Seed test suspicious events with different users, models, risk scores, and time ranges
    events = [
        SuspiciousEvent(
            event_id=f"db-opt-evt-{i+1}",
            user_id="usr-filter-01" if i % 2 == 0 else "usr-filter-02",
            model_id="mdl-filter-01" if i < 3 else "mdl-filter-02",
            timestamp=now - datetime.timedelta(hours=i),
            risk_score=90.0 - (i * 10.0),
            severity="CRITICAL" if i == 0 else ("HIGH" if i < 3 else "LOW"),
            anomaly_score=0.85,
            weight_exfiltration_suspected=(i == 0),
            exfiltration_confidence=0.90 if i == 0 else 0.10,
            production_usage_detected=True,
            reason="Test DB Optimization event",
            evidence=["SQL query optimization test"],
            related_events=[],
            investigation_timeline=[]
        )
        for i in range(5)
    ]

    db_session.add_all(events)
    await db_session.commit()

    # 2. Test User Filtering
    resp_user = await client.get("/api/v1/suspicious-events?user_id=usr-filter-01")
    assert resp_user.status_code == 200
    user_data = resp_user.json()
    assert len(user_data) > 0
    assert all(item["user_id"] == "usr-filter-01" for item in user_data)

    # 3. Test Model Filtering
    resp_model = await client.get("/api/v1/suspicious-events?model_id=mdl-filter-01")
    assert resp_model.status_code == 200
    model_data = resp_model.json()
    assert len(model_data) > 0
    assert all(item["model_id"] == "mdl-filter-01" for item in model_data)

    # 4. Test Risk Score Descending Sorting
    resp_sort = await client.get("/api/v1/suspicious-events")
    assert resp_sort.status_code == 200
    sort_data = resp_sort.json()
    scores = [item["risk_score"] for item in sort_data]
    assert scores == sorted(scores, reverse=True)

    # 5. Test Pagination (skip=1, limit=2)
    resp_page = await client.get("/api/v1/suspicious-events?skip=1&limit=2")
    assert resp_page.status_code == 200
    page_data = resp_page.json()
    assert len(page_data) <= 2
    assert page_data[0]["event_id"] == sort_data[1]["event_id"]

    # 6. Test Empty Result Set Handling
    resp_empty = await client.get("/api/v1/suspicious-events?user_id=nonexistent-user-999")
    assert resp_empty.status_code == 200
    assert resp_empty.json() == []
