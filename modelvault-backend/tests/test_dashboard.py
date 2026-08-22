import uuid
import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_dashboard_endpoints(client: AsyncClient):
    # 1. Create a user and model
    user_res = await client.post("/users", json={
        "username": "triage.officer",
        "email": "triage@modelvault.io",
        "role": "SOC Analyst",
        "department": "Incident Response",
    })
    assert user_res.status_code == 201
    user_id = user_res.json()["id"]

    model_res = await client.post("/models", json={
        "name": "recon-sentinel-v9",
        "description": "Core model",
        "owner_id": user_id,
        "sensitivity_level": "CRITICAL",
    })
    assert model_res.status_code == 201
    model_id = model_res.json()["id"]

    # 2. Ingest access event
    event_res = await client.post("/access-events", json={
        "user_id": user_id,
        "model_id": model_id,
        "action": "download",
        "source": "S3",
        "raw_metadata": {"ip_address": "198.51.100.99", "bytes": 10000},
    })
    assert event_res.status_code == 201
    event_id = event_res.json()["id"]

    # 3. Ingest anomaly
    anom_res = await client.post("/anomaly-results", json={
        "access_event_id": event_id,
        "anomaly_score": 0.95,
        "reason": "Massive download from external IP",
    })
    assert anom_res.status_code == 201

    # 4. Test GET /dashboard/stats
    stats_res = await client.get("/dashboard/stats")
    assert stats_res.status_code == 200
    stats_data = stats_res.json()
    assert "total_models" in stats_data
    assert "flagged_count" in stats_data
    assert "active_anomalies" in stats_data

    # 5. Test GET /dashboard/top-suspicious
    top_res = await client.get("/dashboard/top-suspicious")
    assert top_res.status_code == 200
    top_items = top_res.json()
    assert len(top_items) >= 1
    assert top_items[0]["anomaly_score"] == 0.95
    assert len(top_items[0]["evidence"]) >= 1

    # 6. Test GET /dashboard/flagged-models
    flagged_res = await client.get("/dashboard/flagged-models")
    assert flagged_res.status_code == 200
    assert len(flagged_res.json()) >= 1

    # 7. Test PATCH /flagged-models/{id}/review
    patch_res = await client.patch(f"/flagged-models/{model_id}/review", json={"reviewed": True})
    assert patch_res.status_code == 200
    assert patch_res.json()["reviewed"] is True
