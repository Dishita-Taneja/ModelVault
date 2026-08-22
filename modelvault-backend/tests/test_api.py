import uuid
from datetime import datetime, timedelta, timezone
import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_health_check(client: AsyncClient):
    response = await client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok", "service": "modelvault-backend"}


@pytest.mark.asyncio
async def test_user_crud(client: AsyncClient):
    # 1. Create user
    user_data = {
        "username": "sarah.connor",
        "email": "sarah@cyberdyne.ai",
        "role": "Security Lead",
        "department": "InfoSec",
    }
    create_res = await client.post("/users", json=user_data)
    assert create_res.status_code == 201
    created_user = create_res.json()
    assert created_user["username"] == "sarah.connor"
    assert created_user["email"] == "sarah@cyberdyne.ai"
    assert created_user["role"] == "Security Lead"
    assert created_user["department"] == "InfoSec"
    user_id = created_user["id"]

    # 2. Get user by ID
    get_res = await client.get(f"/users/{user_id}")
    assert get_res.status_code == 200
    assert get_res.json()["id"] == user_id

    # 3. List users with pagination
    list_res = await client.get("/users?skip=0&limit=10")
    assert list_res.status_code == 200
    assert len(list_res.json()) >= 1

    # 4. Duplicate username should fail
    dup_res = await client.post("/users", json=user_data)
    assert dup_res.status_code == 400
    assert "already registered" in dup_res.json()["detail"]

    # 5. Duplicate email should fail
    dup_email_res = await client.post("/users", json={
        "username": "sarah.alternate",
        "email": "sarah@cyberdyne.ai",
    })
    assert dup_email_res.status_code == 400
    assert "already registered" in dup_email_res.json()["detail"]

    # 6. Non-existent user should return 404
    non_existent = str(uuid.uuid4())
    not_found_res = await client.get(f"/users/{non_existent}")
    assert not_found_res.status_code == 404


@pytest.mark.asyncio
async def test_model_crud(client: AsyncClient):
    # 1. Create user first
    user_res = await client.post("/users", json={
        "username": "alex.mercer",
        "email": "alex@genetech.io",
        "role": "ML Engineer",
        "department": "NLP",
    })
    user_id = user_res.json()["id"]

    # 2. Attempt to create model with non-existent owner
    invalid_owner_res = await client.post("/models", json={
        "name": "ghost-model",
        "owner_id": str(uuid.uuid4()),
    })
    assert invalid_owner_res.status_code == 404

    # 3. Create model
    model_data = {
        "name": "sentinel-llm-v1",
        "description": "Proprietary safety filter model",
        "owner_id": user_id,
        "sensitivity_level": "CRITICAL",
    }
    model_res = await client.post("/models", json=model_data)
    assert model_res.status_code == 201
    created_model = model_res.json()
    assert created_model["name"] == "sentinel-llm-v1"
    assert created_model["sensitivity_level"] == "CRITICAL"
    model_id = created_model["id"]

    # 4. Get model by ID
    get_res = await client.get(f"/models/{model_id}")
    assert get_res.status_code == 200
    assert get_res.json()["owner_id"] == user_id

    # 5. Non-existent model returns 404
    not_found_model = await client.get(f"/models/{uuid.uuid4()}")
    assert not_found_model.status_code == 404

    # 6. List models
    list_res = await client.get("/models")
    assert list_res.status_code == 200
    assert any(m["id"] == model_id for m in list_res.json())


@pytest.mark.asyncio
async def test_access_events_and_filtering(client: AsyncClient):
    # 1. Create user and model
    user_res = await client.post("/users", json={
        "username": "dana.scully",
        "email": "dana@fbi.gov",
        "role": "Investigator",
        "department": "Cybercrime",
    })
    user_id = user_res.json()["id"]

    model_res = await client.post("/models", json={
        "name": "x-files-vision",
        "description": "Anomaly vision detector",
        "owner_id": user_id,
        "sensitivity_level": "HIGH",
    })
    model_id = model_res.json()["id"]

    now = datetime.now(timezone.utc)
    t1 = (now - timedelta(hours=2)).isoformat()
    t2 = (now - timedelta(hours=1)).isoformat()
    t3 = now.isoformat()

    # 2. Ingest access events
    event_1 = {
        "user_id": user_id,
        "model_id": model_id,
        "action": "inference",
        "timestamp": t1,
        "source": "API_GATEWAY",
        "raw_metadata": {"ip": "192.168.1.10", "status": "200 OK"},
    }
    event_2 = {
        "user_id": user_id,
        "model_id": model_id,
        "action": "download",
        "timestamp": t2,
        "source": "S3",
        "raw_metadata": {"bytes": 5000000},
    }
    event_3 = {
        "user_id": user_id,
        "model_id": model_id,
        "action": "read",
        "timestamp": t3,
        "source": "IAM",
        "raw_metadata": {"check": "passed"},
    }

    res1 = await client.post("/access-events", json=event_1)
    assert res1.status_code == 201
    assert res1.json()["raw_metadata"]["ip"] == "192.168.1.10"
    event_1_id = res1.json()["id"]

    res2 = await client.post("/access-events", json=event_2)
    assert res2.status_code == 201

    res3 = await client.post("/access-events", json=event_3)
    assert res3.status_code == 201

    # 3. Get single access event by ID
    get_ev_res = await client.get(f"/access-events/{event_1_id}")
    assert get_ev_res.status_code == 200
    assert get_ev_res.json()["action"] == "inference"

    # 4. Ingest with invalid model_id should return 404
    inv_event = await client.post("/access-events", json={
        "user_id": user_id,
        "model_id": str(uuid.uuid4()),
        "action": "read",
    })
    assert inv_event.status_code == 404

    # 5. List access events with user_id filter
    filter_user_res = await client.get(f"/access-events?user_id={user_id}")
    assert filter_user_res.status_code == 200
    assert len(filter_user_res.json()) >= 3

    # 6. List access events with model_id filter
    filter_model_res = await client.get(f"/access-events?model_id={model_id}")
    assert filter_model_res.status_code == 200
    assert len(filter_model_res.json()) >= 3

    # 7. List access events with time range filter
    start_param = (now - timedelta(hours=2, minutes=30)).isoformat()
    end_param = (now - timedelta(minutes=30)).isoformat()
    filter_time_res = await client.get(f"/access-events?start_time={start_param}&end_time={end_param}")
    assert filter_time_res.status_code == 200
    returned_events = filter_time_res.json()
    assert len(returned_events) == 2


@pytest.mark.asyncio
async def test_anomaly_results_and_summary(client: AsyncClient):
    # 1. Setup user, model, and access events
    user_res = await client.post("/users", json={
        "username": "fox.mulder",
        "email": "fox@fbi.gov",
        "role": "Agent",
        "department": "Cybercrime",
    })
    user_id = user_res.json()["id"]

    model_res = await client.post("/models", json={
        "name": "satellite-recon-v4",
        "description": "Classified model",
        "owner_id": user_id,
        "sensitivity_level": "CRITICAL",
    })
    model_id = model_res.json()["id"]

    # Ingest 4 access events
    events = []
    for i in range(4):
        ev_res = await client.post("/access-events", json={
            "user_id": user_id,
            "model_id": model_id,
            "action": "download",
            "source": f"S3_SRC_{i}",
            "raw_metadata": {"index": i, "actor": "unauthorized"},
        })
        assert ev_res.status_code == 201
        events.append(ev_res.json())

    # 2. Ingest anomaly result for non-existent event should return 404
    inv_anom = await client.post("/anomaly-results", json={
        "access_event_id": str(uuid.uuid4()),
        "anomaly_score": 0.99,
    })
    assert inv_anom.status_code == 404

    # 3. Ingest anomaly results via POST /anomaly-results stub endpoint
    anomaly_payloads = [
        {"access_event_id": events[0]["id"], "anomaly_score": 0.45, "reason": "Low suspicion probe"},
        {"access_event_id": events[1]["id"], "anomaly_score": 0.99, "reason": "Critical exfiltration"},
        {"access_event_id": events[2]["id"], "anomaly_score": 0.88, "reason": "High frequency read"},
        {"access_event_id": events[3]["id"], "anomaly_score": 0.92, "reason": "Unauthorized weight dump"},
    ]

    for p in anomaly_payloads:
        post_anom_res = await client.post("/anomaly-results", json=p)
        assert post_anom_res.status_code == 201

    # 4. Test GET /anomaly-results with filters
    list_anom_res = await client.get(f"/anomaly-results?user_id={user_id}&model_id={model_id}")
    assert list_anom_res.status_code == 200
    results = list_anom_res.json()
    assert len(results) == 4

    # 5. Test GET /summary/top-suspicious (default top 3)
    summary_res = await client.get("/summary/top-suspicious")
    assert summary_res.status_code == 200
    top_3 = summary_res.json()
    assert len(top_3) == 3

    # Check that results are sorted in descending order of anomaly_score
    scores = [item["anomaly_score"] for item in top_3]
    assert scores == [0.99, 0.92, 0.88]
    assert top_3[0]["reason"] == "Critical exfiltration"
    assert top_3[0]["access_event"]["id"] == events[1]["id"]
    assert top_3[0]["access_event"]["raw_metadata"]["actor"] == "unauthorized"

    # 6. Test GET /summary/top-suspicious with custom limit
    summary_limit_1 = await client.get("/summary/top-suspicious?limit=1")
    assert summary_limit_1.status_code == 200
    assert len(summary_limit_1.json()) == 1
    assert summary_limit_1.json()[0]["anomaly_score"] == 0.99
