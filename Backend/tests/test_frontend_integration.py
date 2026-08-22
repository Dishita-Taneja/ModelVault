import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

@pytest.mark.asyncio
async def test_frontend_backend_api_integration(client: AsyncClient, db_session: AsyncSession):
    """
    Verifies that all 16 endpoints consumed by ModelVault frontend
    work seamlessly against real ingested data.
    """
    # 1. Run complete analysis pipeline first to populate DB
    run_resp = await client.post("/api/v1/analysis/run")
    assert run_resp.status_code == 200

    # 2. GET /api/v1/dashboard/summary
    resp_summary = await client.get("/api/v1/dashboard/summary")
    assert resp_summary.status_code == 200
    summary_json = resp_summary.json()
    assert summary_json["total_models"] >= 1
    assert summary_json["total_users"] >= 1
    assert summary_json["total_events"] >= 1

    # 3. GET /api/v1/dashboard/top-suspicious
    resp_top = await client.get("/api/v1/dashboard/top-suspicious")
    assert resp_top.status_code == 200
    assert isinstance(resp_top.json(), list)

    # 4. GET /api/v1/suspicious-events
    resp_se = await client.get("/api/v1/suspicious-events")
    assert resp_se.status_code == 200
    se_list = resp_se.json()
    assert isinstance(se_list, list)
    assert len(se_list) >= 1

    first_event_id = se_list[0]["event_id"]
    first_model_id = se_list[0]["model_id"]
    first_user_id = se_list[0]["user_id"]

    # 5. GET /api/v1/suspicious-events/{id}
    resp_se_detail = await client.get(f"/api/v1/suspicious-events/{first_event_id}")
    assert resp_se_detail.status_code == 200
    assert resp_se_detail.json()["event_id"] == first_event_id

    # 6. GET /api/v1/models
    resp_models = await client.get("/api/v1/models")
    assert resp_models.status_code == 200
    assert len(resp_models.json()) >= 1

    # 7. GET /api/v1/models/{id}
    resp_model_detail = await client.get(f"/api/v1/models/{first_model_id}")
    assert resp_model_detail.status_code == 200

    # 8. GET /api/v1/models/{id}/investigation
    resp_model_inv = await client.get(f"/api/v1/models/{first_model_id}/investigation")
    assert resp_model_inv.status_code == 200
    assert "timeline" in resp_model_inv.json()

    # 9. GET /api/v1/users
    resp_users = await client.get("/api/v1/users")
    assert resp_users.status_code == 200
    assert len(resp_users.json()) >= 1

    # 10. GET /api/v1/users/{id}/investigation
    resp_user_inv = await client.get(f"/api/v1/users/{first_user_id}/investigation")
    assert resp_user_inv.status_code == 200
    assert "timeline" in resp_user_inv.json()

    # 11. GET /api/v1/events
    resp_events = await client.get("/api/v1/events")
    assert resp_events.status_code == 200
    assert len(resp_events.json()) >= 1

    # 12. GET /api/v1/anomalies
    resp_anom = await client.get("/api/v1/anomalies")
    assert resp_anom.status_code == 200
    assert isinstance(resp_anom.json(), list)

    # 13. GET /api/v1/anomalies/top
    resp_top_anom = await client.get("/api/v1/anomalies/top?limit=3")
    assert resp_top_anom.status_code == 200
    assert isinstance(resp_top_anom.json(), list)

    # 14. GET /api/v1/investigations/event/{id}
    resp_event_inv = await client.get(f"/api/v1/investigations/event/{first_event_id}")
    assert resp_event_inv.status_code == 200
    assert "timeline" in resp_event_inv.json()

    # 15. GET /api/v1/investigations/model/{id}
    resp_inv_m = await client.get(f"/api/v1/investigations/model/{first_model_id}")
    assert resp_inv_m.status_code == 200

    # 16. GET /api/v1/investigations/user/{id}
    resp_inv_u = await client.get(f"/api/v1/investigations/user/{first_user_id}")
    assert resp_inv_u.status_code == 200
