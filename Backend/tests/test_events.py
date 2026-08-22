import pytest
import datetime
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_create_and_query_alerts(client: AsyncClient):
    # Create an alert
    alert_payload = {
        "alert_id": "alt-test-01",
        "event_id": "evt-test-01",
        "model_id": "mdl-test-01",
        "user_arn": "arn:aws:iam::123456789012:user/bad.actor",
        "risk_score": 0.99,
        "severity": "CRITICAL",
        "title": "Model Weights Exfiltration Attempt",
        "description": "Suspicious large download of model weights from untrusted IP.",
        "status": "OPEN"
    }

    create_resp = await client.post("/api/v1/alerts/", json=alert_payload)
    assert create_resp.status_code == 201

    top_resp = await client.get("/api/v1/alerts/top-suspicious")
    assert top_resp.status_code == 200
    alerts = top_resp.json()
    assert len(alerts) >= 1
    assert alerts[0]["alert_id"] == "alt-test-01"
    assert alerts[0]["risk_score"] == 0.99
