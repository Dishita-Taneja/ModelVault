import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession


@pytest.mark.asyncio
async def test_frontend_api_contract_endpoints(client: AsyncClient, db_session: AsyncSession):
    # 1. Run complete analysis pipeline first to populate DB
    run_resp = await client.post("/api/v1/analysis/run")
    assert run_resp.status_code == 200

    # 2. GET /api/v1/dashboard/summary
    summary_resp = await client.get("/api/v1/dashboard/summary")
    assert summary_resp.status_code == 200
    summary_data = summary_resp.json()
    assert summary_data["total_models"] == 3
    assert summary_data["total_users"] == 3
    assert summary_data["total_events"] == 9
    assert summary_data["suspicious_events"] == 9
    assert summary_data["exfiltration_suspected_events"] >= 1
    assert len(summary_data["top_suspicious_events"]) == 3

    # 3. GET /api/v1/dashboard/top-suspicious
    top_dash_resp = await client.get("/api/v1/dashboard/top-suspicious")
    assert top_dash_resp.status_code == 200
    assert len(top_dash_resp.json()) == 3

    # 4. GET /api/v1/models & GET /api/v1/models/{id} & investigation
    models_resp = await client.get("/api/v1/models")
    assert models_resp.status_code == 200
    assert len(models_resp.json()) == 3

    model_detail_resp = await client.get("/api/v1/models/mdl-llm-01")
    assert model_detail_resp.status_code == 200
    assert model_detail_resp.json()["model_id"] == "mdl-llm-01"

    model_inv_resp = await client.get("/api/v1/models/mdl-llm-01/investigation")
    assert model_inv_resp.status_code == 200
    assert model_inv_resp.json()["target_id"] == "mdl-llm-01"

    # 5. GET /api/v1/users & GET /api/v1/users/{id}/investigation
    users_resp = await client.get("/api/v1/users")
    assert users_resp.status_code == 200
    assert len(users_resp.json()) == 3

    user_inv_resp = await client.get("/api/v1/users/usr-003/investigation")
    assert user_inv_resp.status_code == 200
    assert user_inv_resp.json()["target_id"] == "usr-003"

    # 6. GET /api/v1/events & GET /api/v1/events/{id}
    events_resp = await client.get("/api/v1/events?source=S3")
    assert events_resp.status_code == 200
    assert len(events_resp.json()) == 2

    event_detail_resp = await client.get("/api/v1/events/s3-evt-302")
    assert event_detail_resp.status_code == 200
    assert event_detail_resp.json()["event_id"] == "s3-evt-302"

    # 7. GET /api/v1/anomalies & GET /api/v1/anomalies/top
    anom_resp = await client.get("/api/v1/anomalies")
    assert anom_resp.status_code == 200
    assert isinstance(anom_resp.json(), list)

    top_anom_resp = await client.get("/api/v1/anomalies/top?limit=3")
    assert top_anom_resp.status_code == 200
    assert isinstance(top_anom_resp.json(), list)

    # 8. GET /api/v1/suspicious-events & GET /api/v1/suspicious-events/{id}
    se_resp = await client.get("/api/v1/suspicious-events?severity=CRITICAL")
    assert se_resp.status_code == 200
    assert len(se_resp.json()) >= 1

    se_detail_resp = await client.get("/api/v1/suspicious-events/s3-evt-302")
    assert se_detail_resp.status_code == 200
    assert se_detail_resp.json()["event_id"] == "s3-evt-302"

    # 9. GET /api/v1/investigations/event/{id}, model/{id}, user/{id}
    inv_evt_resp = await client.get("/api/v1/investigations/event/s3-evt-302")
    assert inv_evt_resp.status_code == 200

    inv_mdl_resp = await client.get("/api/v1/investigations/model/mdl-llm-01")
    assert inv_mdl_resp.status_code == 200

    inv_usr_resp = await client.get("/api/v1/investigations/user/usr-003")
    assert inv_usr_resp.status_code == 200
