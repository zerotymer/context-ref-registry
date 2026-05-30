"""Tests for POST /validate-references endpoint."""
import uuid

import pytest
from httpx import AsyncClient


async def _create_entity(admin_client: AsyncClient, etype: str, name: str, status: str = "active") -> dict:
    r = await admin_client.post("/entities", json={"type": etype, "canonical_name": name, "status": status})
    assert r.status_code == 201
    return r.json()["data"]


async def _add_alias(admin_client: AsyncClient, entity_id: str, alias: str, locale: str = "en") -> None:
    r = await admin_client.post(f"/entities/{entity_id}/aliases", json={"locale": locale, "alias": alias})
    assert r.status_code == 201


@pytest.mark.asyncio
async def test_validate_valid_uuid(admin_client: AsyncClient):
    entity = await _create_entity(admin_client, "FEATURE", "결제 기능")
    r = await admin_client.post("/validate-references", json={"references": [entity["id"]]})
    assert r.status_code == 200
    data = r.json()["data"]
    assert data["valid"] is True
    assert len(data["resolved"]) == 1
    assert data["resolved"][0]["id"] == entity["id"]
    assert data["resolved"][0]["canonical_name"] == "결제 기능"
    assert data["resolved"][0]["entity_status"] == "active"
    assert data["missing"] == []
    assert data["ambiguous"] == []


@pytest.mark.asyncio
async def test_validate_unknown_uuid(admin_client: AsyncClient):
    fake_id = str(uuid.uuid4())
    r = await admin_client.post("/validate-references", json={"references": [fake_id]})
    assert r.status_code == 200
    data = r.json()["data"]
    assert data["valid"] is False
    assert data["missing"] == [fake_id]
    assert data["resolved"] == []


@pytest.mark.asyncio
async def test_validate_alias_resolved(admin_client: AsyncClient):
    entity = await _create_entity(admin_client, "UI_AREA", "검색 영역")
    await _add_alias(admin_client, entity["id"], "search-area")
    r = await admin_client.post("/validate-references", json={"references": ["search-area"]})
    assert r.status_code == 200
    data = r.json()["data"]
    assert data["valid"] is True
    assert len(data["resolved"]) == 1
    assert data["resolved"][0]["id"] == entity["id"]
    assert data["resolved"][0]["input"] == "search-area"


@pytest.mark.asyncio
async def test_validate_alias_not_found(admin_client: AsyncClient):
    r = await admin_client.post("/validate-references", json={"references": ["nonexistent-alias"]})
    assert r.status_code == 200
    data = r.json()["data"]
    assert data["valid"] is False
    assert "nonexistent-alias" in data["missing"]


@pytest.mark.asyncio
async def test_validate_ambiguous_alias(admin_client: AsyncClient):
    e1 = await _create_entity(admin_client, "FEATURE", "기능 A")
    e2 = await _create_entity(admin_client, "FEATURE", "기능 B")
    await _add_alias(admin_client, e1["id"], "shared-alias")
    await _add_alias(admin_client, e2["id"], "shared-alias")
    r = await admin_client.post("/validate-references", json={"references": ["shared-alias"]})
    assert r.status_code == 200
    data = r.json()["data"]
    assert data["valid"] is False
    assert len(data["ambiguous"]) == 1
    ambig = data["ambiguous"][0]
    assert ambig["input"] == "shared-alias"
    assert e1["id"] in ambig["candidates"]
    assert e2["id"] in ambig["candidates"]


@pytest.mark.asyncio
async def test_validate_mixed_references(admin_client: AsyncClient):
    entity = await _create_entity(admin_client, "INFRA_UNIT", "DB 서버")
    await _add_alias(admin_client, entity["id"], "db-server")
    fake_id = str(uuid.uuid4())
    r = await admin_client.post("/validate-references", json={"references": [entity["id"], "db-server", fake_id, "bad-alias"]})
    assert r.status_code == 200
    data = r.json()["data"]
    assert data["valid"] is False
    # entity["id"] and "db-server" both resolve to same entity
    assert len(data["resolved"]) == 2
    assert fake_id in data["missing"]
    assert "bad-alias" in data["missing"]


@pytest.mark.asyncio
async def test_validate_empty_references(admin_client: AsyncClient):
    r = await admin_client.post("/validate-references", json={"references": []})
    assert r.status_code == 200
    data = r.json()["data"]
    assert data["valid"] is True
    assert data["resolved"] == []
    assert data["ambiguous"] == []
    assert data["missing"] == []


@pytest.mark.asyncio
async def test_validate_deprecated_entity_still_resolved(admin_client: AsyncClient):
    entity = await _create_entity(admin_client, "FEATURE", "구형 기능", status="deprecated")
    r = await admin_client.post("/validate-references", json={"references": [entity["id"]]})
    assert r.status_code == 200
    data = r.json()["data"]
    assert data["valid"] is True
    assert len(data["resolved"]) == 1
    assert data["resolved"][0]["entity_status"] == "deprecated"


@pytest.mark.asyncio
async def test_validate_response_structure(admin_client: AsyncClient):
    r = await admin_client.post("/validate-references", json={"references": []})
    assert r.status_code == 200
    body = r.json()
    assert body["ok"] is True
    assert "data" in body
    data = body["data"]
    assert "valid" in data
    assert "resolved" in data
    assert "ambiguous" in data
    assert "missing" in data
