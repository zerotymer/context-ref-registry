"""Tests for GET /export/openapi endpoint."""
import pytest
from httpx import AsyncClient


async def _create_entity(admin_client: AsyncClient, etype: str, name: str, status: str = "active") -> dict:
    r = await admin_client.post("/entities", json={"type": etype, "canonical_name": name, "status": status})
    assert r.status_code == 201
    return r.json()["data"]


async def _add_context(admin_client: AsyncClient, entity_id: str, context_type: str, body: str) -> None:
    r = await admin_client.post(
        f"/entities/{entity_id}/contexts",
        json={"context_type": context_type, "body": body, "language": "ko"},
    )
    assert r.status_code == 201


@pytest.mark.asyncio
async def test_openapi_returns_json(admin_client: AsyncClient):
    await _create_entity(admin_client, "API", "GET /users")
    r = await admin_client.get("/export/openapi")
    assert r.status_code == 200
    assert "application/json" in r.headers["content-type"]
    spec = r.json()
    assert spec["openapi"] == "3.1.0"


@pytest.mark.asyncio
async def test_openapi_returns_yaml(admin_client: AsyncClient):
    await _create_entity(admin_client, "API", "GET /health")
    r = await admin_client.get("/export/openapi?format=yaml")
    assert r.status_code == 200
    assert "yaml" in r.headers["content-type"]
    assert "openapi: 3.1.0" in r.text


@pytest.mark.asyncio
async def test_openapi_only_includes_api_entities(admin_client: AsyncClient):
    await _create_entity(admin_client, "API", "GET /orders")
    await _create_entity(admin_client, "FEATURE", "주문 처리 기능")

    r = await admin_client.get("/export/openapi")
    assert r.status_code == 200
    spec = r.json()
    assert "/orders" in spec["paths"]
    # FEATURE entity should not appear as a path
    assert "/주문-처리-기능" not in spec["paths"]


@pytest.mark.asyncio
async def test_openapi_parses_method_and_path_from_canonical_name(admin_client: AsyncClient):
    await _create_entity(admin_client, "API", "POST /items/{id}/comments")
    r = await admin_client.get("/export/openapi")
    assert r.status_code == 200
    spec = r.json()
    assert "/items/{id}/comments" in spec["paths"]
    assert "post" in spec["paths"]["/items/{id}/comments"]


@pytest.mark.asyncio
async def test_openapi_fallback_slugified_path(admin_client: AsyncClient):
    await _create_entity(admin_client, "API", "사용자 목록 조회")
    r = await admin_client.get("/export/openapi")
    assert r.status_code == 200
    spec = r.json()
    assert "get" in list(list(spec["paths"].values())[0].keys())


@pytest.mark.asyncio
async def test_openapi_summary_context_maps_to_summary(admin_client: AsyncClient):
    entity = await _create_entity(admin_client, "API", "GET /products")
    await _add_context(admin_client, entity["id"], "summary", "상품 목록을 반환합니다.")
    r = await admin_client.get("/export/openapi")
    assert r.status_code == 200
    spec = r.json()
    operation = spec["paths"]["/products"]["get"]
    assert operation["summary"] == "상품 목록을 반환합니다."


@pytest.mark.asyncio
async def test_openapi_details_context_maps_to_description(admin_client: AsyncClient):
    entity = await _create_entity(admin_client, "API", "GET /reviews")
    await _add_context(admin_client, entity["id"], "details", "페이지네이션을 지원합니다.")
    r = await admin_client.get("/export/openapi")
    assert r.status_code == 200
    spec = r.json()
    operation = spec["paths"]["/reviews"]["get"]
    assert "페이지네이션을 지원합니다." in operation["description"]


@pytest.mark.asyncio
async def test_openapi_excludes_deprecated_by_default(admin_client: AsyncClient):
    await _create_entity(admin_client, "API", "GET /legacy", status="deprecated")
    await _create_entity(admin_client, "API", "GET /current")
    r = await admin_client.get("/export/openapi")
    assert r.status_code == 200
    spec = r.json()
    assert "/legacy" not in spec["paths"]
    assert "/current" in spec["paths"]


@pytest.mark.asyncio
async def test_openapi_includes_deprecated_when_requested(admin_client: AsyncClient):
    await _create_entity(admin_client, "API", "DELETE /old-api", status="deprecated")
    r = await admin_client.get("/export/openapi?include_deprecated=true")
    assert r.status_code == 200
    spec = r.json()
    assert "/old-api" in spec["paths"]
    assert spec["paths"]["/old-api"]["delete"]["deprecated"] is True


@pytest.mark.asyncio
async def test_openapi_default_response_added(admin_client: AsyncClient):
    await _create_entity(admin_client, "API", "GET /ping")
    r = await admin_client.get("/export/openapi")
    assert r.status_code == 200
    spec = r.json()
    operation = spec["paths"]["/ping"]["get"]
    assert "responses" in operation
    assert "200" in operation["responses"]


@pytest.mark.asyncio
async def test_openapi_info_fields(admin_client: AsyncClient):
    await _create_entity(admin_client, "API", "GET /info")
    r = await admin_client.get("/export/openapi?title=My+API&version=1.0")
    assert r.status_code == 200
    spec = r.json()
    assert spec["info"]["title"] == "My API"
    assert spec["info"]["version"] == "1.0"
