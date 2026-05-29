"""Context bundle endpoint tests."""
import uuid

import pytest
from httpx import AsyncClient


async def _create_entity(admin_client: AsyncClient, etype: str, name: str, status: str = "active") -> dict:
    r = await admin_client.post("/entities", json={"type": etype, "canonical_name": name, "status": status})
    assert r.status_code == 201
    return r.json()["data"]


async def _create_relation(admin_client: AsyncClient, from_id: str, to_id: str, rtype: str) -> dict:
    r = await admin_client.post(
        "/relations",
        json={"from_entity_id": from_id, "to_entity_id": to_id, "relation_type": rtype},
    )
    assert r.status_code == 201
    return r.json()["data"]


async def _add_context(admin_client: AsyncClient, entity_id: str, context_type: str, body: str) -> dict:
    r = await admin_client.post(
        f"/entities/{entity_id}/contexts",
        json={"context_type": context_type, "body": body, "language": "ko"},
    )
    assert r.status_code == 201
    return r.json()["data"]


@pytest.mark.asyncio
async def test_bundle_includes_root_and_depth1_entity(admin_client: AsyncClient):
    root = await _create_entity(admin_client, "FEATURE", "Root Feature")
    related = await _create_entity(admin_client, "UI_AREA", "Related UI Area")
    await _create_relation(admin_client, root["id"], related["id"], "RELATED_TO")

    r = await admin_client.post(
        "/context-bundle",
        json={"root_ids": [root["id"]], "max_depth": 1, "token_budget": 6000, "language": "ko"},
    )
    assert r.status_code == 200
    data = r.json()["data"]
    all_ids = {e["id"] for e in data["roots"]} | {e["id"] for e in data["entities"]}
    assert root["id"] in all_ids
    assert related["id"] in all_ids
    assert len(data["relations"]) == 1


@pytest.mark.asyncio
async def test_bundle_max_depth_zero_returns_only_roots(admin_client: AsyncClient):
    root = await _create_entity(admin_client, "FEATURE", "Root Only")
    related = await _create_entity(admin_client, "UI_AREA", "Not Included")
    await _create_relation(admin_client, root["id"], related["id"], "RELATED_TO")

    r = await admin_client.post(
        "/context-bundle",
        json={"root_ids": [root["id"]], "max_depth": 0, "token_budget": 6000, "language": "ko"},
    )
    assert r.status_code == 200
    data = r.json()["data"]
    assert len(data["roots"]) == 1
    assert data["roots"][0]["id"] == root["id"]
    assert data["entities"] == []
    assert data["relations"] == []


@pytest.mark.asyncio
async def test_bundle_deprecated_entity_produces_warning(admin_client: AsyncClient):
    root = await _create_entity(admin_client, "FEATURE", "Deprecated Root", status="deprecated")

    r = await admin_client.post(
        "/context-bundle",
        json={"root_ids": [root["id"]], "max_depth": 1, "token_budget": 6000, "language": "ko"},
    )
    assert r.status_code == 200
    data = r.json()["data"]
    assert len(data["warnings"]) == 1
    assert data["warnings"][0]["entity_id"] == root["id"]
    assert data["warnings"][0]["type"] == "deprecated_entity"


@pytest.mark.asyncio
async def test_bundle_token_budget_excludes_low_priority_contexts(admin_client: AsyncClient):
    root = await _create_entity(admin_client, "FEATURE", "Budget Test")
    await _add_context(admin_client, root["id"], "exception_case", "x" * 500)
    await _add_context(admin_client, root["id"], "summary", "Short summary")

    r = await admin_client.post(
        "/context-bundle",
        json={"root_ids": [root["id"]], "max_depth": 1, "token_budget": 100, "language": "ko"},
    )
    assert r.status_code == 200
    data = r.json()["data"]
    context_types = [c["context_type"] for c in data["contexts"]]
    assert "summary" in context_types
    assert "exception_case" not in context_types


@pytest.mark.asyncio
async def test_bundle_root_not_found_returns_404(client: AsyncClient):
    r = await client.post(
        "/context-bundle",
        json={"root_ids": [str(uuid.uuid4())], "max_depth": 1, "token_budget": 6000, "language": "ko"},
    )
    assert r.status_code == 404
    assert r.json()["ok"] is False


@pytest.mark.asyncio
async def test_bundle_multiple_roots(admin_client: AsyncClient):
    root1 = await _create_entity(admin_client, "FEATURE", "Feature A")
    root2 = await _create_entity(admin_client, "UI_AREA", "UI Area B")

    r = await admin_client.post(
        "/context-bundle",
        json={
            "root_ids": [root1["id"], root2["id"]],
            "max_depth": 1,
            "token_budget": 6000,
            "language": "ko",
        },
    )
    assert r.status_code == 200
    data = r.json()["data"]
    root_ids = {e["id"] for e in data["roots"]}
    assert root1["id"] in root_ids
    assert root2["id"] in root_ids


@pytest.mark.asyncio
async def test_bundle_include_relations_filter(admin_client: AsyncClient):
    root = await _create_entity(admin_client, "FEATURE", "Root Feature")
    related_uses = await _create_entity(admin_client, "INFRA_UNIT", "Infra Unit")
    related_calls = await _create_entity(admin_client, "API", "API Entity")
    await _create_relation(admin_client, root["id"], related_uses["id"], "USES")
    await _create_relation(admin_client, root["id"], related_calls["id"], "CALLS")

    r = await admin_client.post(
        "/context-bundle",
        json={
            "root_ids": [root["id"]],
            "include_relations": ["USES"],
            "max_depth": 1,
            "token_budget": 6000,
            "language": "ko",
        },
    )
    assert r.status_code == 200
    data = r.json()["data"]
    all_ids = {e["id"] for e in data["roots"]} | {e["id"] for e in data["entities"]}
    assert related_uses["id"] in all_ids
    assert related_calls["id"] not in all_ids
