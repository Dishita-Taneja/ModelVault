import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_create_and_get_model(client: AsyncClient):
    payload = {
        "model_id": "test-mdl-01",
        "name": "Test LLM",
        "description": "Test LLaMA model",
        "framework": "PyTorch",
        "s3_uri": "s3://test-bucket/model.bin",
        "sensitivity_level": "CRITICAL",
        "owner_email": "test@modelvault.io"
    }

    create_resp = await client.post("/api/v1/models/", json=payload)
    assert create_resp.status_code == 201
    created_data = create_resp.json()
    assert created_data["model_id"] == "test-mdl-01"
    assert created_data["name"] == "Test LLM"

    get_resp = await client.get("/api/v1/models/test-mdl-01")
    assert get_resp.status_code == 200
    assert get_resp.json()["model_id"] == "test-mdl-01"


@pytest.mark.asyncio
async def test_get_nonexistent_model(client: AsyncClient):
    resp = await client.get("/api/v1/models/nonexistent-id")
    assert resp.status_code == 404
    data = resp.json()
    assert data["error"]["code"] == "RESOURCE_NOT_FOUND"
