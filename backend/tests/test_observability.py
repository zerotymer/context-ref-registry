"""Tests for Step 2-4: Observability — request logging middleware and /health endpoint."""
import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_health_ok(client: AsyncClient):
    res = await client.get("/health")
    assert res.status_code == 200
    body = res.json()
    assert body["ok"] is True
    assert body["data"]["status"] == "healthy"
    assert body["data"]["db"] == "ok"


@pytest.mark.asyncio
async def test_health_returns_request_id_header(client: AsyncClient):
    res = await client.get("/health")
    assert "x-request-id" in res.headers
    request_id = res.headers["x-request-id"]
    # Basic UUID4 format check
    assert len(request_id) == 36
    assert request_id.count("-") == 4


@pytest.mark.asyncio
async def test_middleware_adds_request_id_to_all_responses(client: AsyncClient):
    for path in ["/health", "/entities", "/search?q=test"]:
        res = await client.get(path)
        assert "x-request-id" in res.headers, f"Missing X-Request-ID on {path}"


@pytest.mark.asyncio
async def test_request_ids_are_unique(client: AsyncClient):
    r1 = await client.get("/health")
    r2 = await client.get("/health")
    assert r1.headers["x-request-id"] != r2.headers["x-request-id"]
