"""Tests for MCP tool implementations.

Tools are called directly via mcp.call_tool() so no MCP transport is needed.
The test DB is shared with other test modules via conftest.py fixtures.
"""
from __future__ import annotations

import json
import uuid

import pytest
from httpx import ASGITransport, AsyncClient

from app.db.session import async_session_factory
from app.main import app
from app.mcp.server import mcp
from app.service.auth_service import AuthService


@pytest.fixture
async def admin_client():
    """Admin-authenticated client for MCP test setup."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        async with async_session_factory() as session:
            await AuthService(session).create_user(
                email="admin@mcptest.com",
                password="admin123",
                display_name="MCP Admin",
                role="admin",
            )
        resp = await ac.post("/auth/login", json={"email": "admin@mcptest.com", "password": "admin123"})
        assert resp.status_code == 200, resp.text
        yield ac


async def _post(admin_client: AsyncClient, path: str, body: dict):
    resp = await admin_client.post(path, json=body)
    assert resp.status_code in (200, 201), resp.text
    return resp.json()["data"]


async def _call(tool_name: str, args: dict) -> dict:
    """Call an MCP tool and parse the JSON result from ContentBlock."""
    blocks = await mcp.call_tool(tool_name, args)
    if isinstance(blocks, (list, tuple)) and blocks:
        first = blocks[0] if not isinstance(blocks[0], (list, tuple)) else blocks[0][0]
        return json.loads(first.text)
    return blocks  # type: ignore[return-value]


# ---------------------------------------------------------------------------
# resolve_alias
# ---------------------------------------------------------------------------


class TestResolveAlias:
    async def test_not_found(self):
        result = await _call("resolve_alias", {"alias": "존재하지않는alias"})
        assert result["status"] == "not_found"

    async def test_resolved(self, admin_client: AsyncClient):
        entity = await _post(admin_client, "/entities", {
            "type": "FEATURE", "canonical_name": "사용자 검색"
        })
        await _post(admin_client, f"/entities/{entity['id']}/aliases", {
            "locale": "ko", "alias": "회원 검색"
        })

        result = await _call("resolve_alias", {"alias": "회원 검색", "locale": "ko"})
        assert result["status"] == "resolved"
        assert result["entity"]["id"] == entity["id"]

    async def test_ambiguous(self, admin_client: AsyncClient):
        e1 = await _post(admin_client, "/entities", {"type": "FEATURE", "canonical_name": "검색 A"})
        e2 = await _post(admin_client, "/entities", {"type": "FEATURE", "canonical_name": "검색 B"})
        for eid in [e1["id"], e2["id"]]:
            await _post(admin_client, f"/entities/{eid}/aliases", {"locale": "ko", "alias": "검색"})

        result = await _call("resolve_alias", {"alias": "검색"})
        assert result["status"] == "ambiguous"
        assert len(result["candidates"]) == 2
        assert result["required_action"] == "ask_user_to_choose_entity_id"


# ---------------------------------------------------------------------------
# get_entity
# ---------------------------------------------------------------------------


class TestGetEntity:
    async def test_found(self, admin_client: AsyncClient):
        entity = await _post(admin_client, "/entities", {
            "type": "UI_AREA", "canonical_name": "검색 조건 영역"
        })
        await _post(admin_client, f"/entities/{entity['id']}/aliases", {
            "locale": "ko", "alias": "검색조건"
        })

        result = await _call("get_entity", {"id": entity["id"]})
        assert result["entity"]["id"] == entity["id"]
        assert result["entity"]["type"] == "UI_AREA"
        assert "ko" in result["aliases"]
        assert "검색조건" in result["aliases"]["ko"]

    async def test_not_found(self):
        result = await _call("get_entity", {"id": str(uuid.uuid4())})
        assert result.get("error") == "ENTITY_NOT_FOUND"

    async def test_deprecated_warning(self, admin_client: AsyncClient):
        e1 = await _post(admin_client, "/entities", {"type": "FEATURE", "canonical_name": "구 기능"})
        e2 = await _post(admin_client, "/entities", {"type": "FEATURE", "canonical_name": "신 기능"})
        await admin_client.patch(f"/entities/{e1['id']}", json={
            "status": "deprecated", "replacement_entity_id": e2["id"]
        })

        result = await _call("get_entity", {"id": e1["id"]})
        assert result["entity"]["status"] == "deprecated"
        assert len(result["warnings"]) == 1
        assert result["warnings"][0]["replacement_entity_id"] == e2["id"]


# ---------------------------------------------------------------------------
# search_entities
# ---------------------------------------------------------------------------


class TestSearchEntities:
    async def test_alias_exact(self, admin_client: AsyncClient):
        entity = await _post(admin_client, "/entities", {"type": "FEATURE", "canonical_name": "기능 X"})
        await _post(admin_client, f"/entities/{entity['id']}/aliases", {
            "locale": "ko", "alias": "정확한alias"
        })

        result = await _call("search_entities", {"query": "정확한alias"})
        ids = [r["id"] for r in result["results"]]
        assert entity["id"] in ids
        matching = next(r for r in result["results"] if r["id"] == entity["id"])
        assert matching["match_reason"] == "alias_exact"

    async def test_canonical_name_partial(self, admin_client: AsyncClient):
        entity = await _post(admin_client, "/entities", {"type": "UI_AREA", "canonical_name": "사용자 목록 화면"})

        result = await _call("search_entities", {"query": "목록 화면"})
        ids = [r["id"] for r in result["results"]]
        assert entity["id"] in ids

    async def test_type_filter(self, admin_client: AsyncClient):
        feat = await _post(admin_client, "/entities", {"type": "FEATURE", "canonical_name": "공통 기능"})
        area = await _post(admin_client, "/entities", {"type": "UI_AREA", "canonical_name": "공통 영역"})

        result = await _call("search_entities", {"query": "공통", "types": ["FEATURE"]})
        ids = [r["id"] for r in result["results"]]
        assert feat["id"] in ids
        assert area["id"] not in ids


# ---------------------------------------------------------------------------
# get_context_bundle
# ---------------------------------------------------------------------------


class TestGetContextBundle:
    async def test_bundle_root_only(self, admin_client: AsyncClient):
        entity = await _post(admin_client, "/entities", {"type": "FEATURE", "canonical_name": "번들 루트"})
        await _post(admin_client, f"/entities/{entity['id']}/contexts", {
            "context_type": "summary", "body": "번들 요약 내용", "language": "ko"
        })

        result = await _call("get_context_bundle", {
            "root_ids": [entity["id"]],
            "max_depth": 0,
        })
        assert len(result["roots"]) == 1
        assert result["roots"][0]["id"] == entity["id"]
        assert len(result["contexts"]) == 1
        assert result["contexts"][0]["body"] == "번들 요약 내용"

    async def test_bundle_with_related(self, admin_client: AsyncClient):
        root = await _post(admin_client, "/entities", {"type": "FEATURE", "canonical_name": "루트 기능"})
        child = await _post(admin_client, "/entities", {"type": "INFRA_UNIT", "canonical_name": "연관 인프라"})
        await _post(admin_client, "/relations", {
            "from_entity_id": root["id"],
            "to_entity_id": child["id"],
            "relation_type": "USES",
        })

        result = await _call("get_context_bundle", {
            "root_ids": [root["id"]],
            "max_depth": 1,
        })
        all_ids = {e["id"] for e in result["roots"] + result["entities"]}
        assert root["id"] in all_ids
        assert child["id"] in all_ids

    async def test_bundle_deprecated_warning(self, admin_client: AsyncClient):
        old = await _post(admin_client, "/entities", {"type": "FEATURE", "canonical_name": "구 기능"})
        new = await _post(admin_client, "/entities", {"type": "FEATURE", "canonical_name": "신 기능"})
        await admin_client.patch(f"/entities/{old['id']}", json={
            "status": "deprecated", "replacement_entity_id": new["id"]
        })

        result = await _call("get_context_bundle", {"root_ids": [old["id"]]})
        assert len(result["warnings"]) == 1
        assert result["warnings"][0]["entity_id"] == old["id"]

    async def test_entity_not_found(self):
        result = await _call("get_context_bundle", {"root_ids": [str(uuid.uuid4())]})
        assert result.get("error") == "ENTITY_NOT_FOUND"


# ---------------------------------------------------------------------------
# validate_references
# ---------------------------------------------------------------------------


class TestValidateReferences:
    async def test_all_resolved(self, admin_client: AsyncClient):
        entity = await _post(admin_client, "/entities", {"type": "FEATURE", "canonical_name": "검증 기능"})
        await _post(admin_client, f"/entities/{entity['id']}/aliases", {
            "locale": "ko", "alias": "검증alias"
        })

        result = await _call("validate_references", {
            "references": [entity["id"], "검증alias"]
        })
        assert result["valid"] is True
        assert len(result["resolved"]) == 2
        assert result["ambiguous"] == []
        assert result["missing"] == []

    async def test_missing_uuid(self):
        fake_id = str(uuid.uuid4())
        result = await _call("validate_references", {"references": [fake_id]})
        assert result["valid"] is False
        assert fake_id in result["missing"]

    async def test_ambiguous_alias(self, admin_client: AsyncClient):
        e1 = await _post(admin_client, "/entities", {"type": "FEATURE", "canonical_name": "중복 기능 A"})
        e2 = await _post(admin_client, "/entities", {"type": "FEATURE", "canonical_name": "중복 기능 B"})
        for eid in [e1["id"], e2["id"]]:
            await _post(admin_client, f"/entities/{eid}/aliases", {"locale": "ko", "alias": "중복alias"})

        result = await _call("validate_references", {"references": ["중복alias"]})
        assert result["valid"] is False
        assert len(result["ambiguous"]) == 1
        assert len(result["ambiguous"][0]["candidates"]) == 2
