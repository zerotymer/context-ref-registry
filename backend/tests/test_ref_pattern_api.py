"""Tests for the three reference patterns: UUID / PROJECT_ID@UUID / PROJECT_ID@TAG."""
from __future__ import annotations

import pytest
from httpx import AsyncClient


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

async def _ensure_project(client: AsyncClient, project_id: str) -> None:
    resp = await client.post("/projects", json={"id": project_id, "alias": project_id})
    # 201 = created, 409 = already exists in this test session
    assert resp.status_code in (201, 409), resp.text


async def _create_entity(client: AsyncClient, **kwargs) -> str:
    project_id = kwargs.get("project_id")
    if project_id:
        await _ensure_project(client, project_id)
    payload = {
        "type": "FEATURE",
        "canonical_name": kwargs.get("canonical_name", "test entity"),
        "status": "active",
    }
    if project_id:
        payload["project_id"] = project_id
    resp = await client.post("/entities", json=payload)
    assert resp.status_code == 201, resp.text
    return resp.json()["data"]["id"]


async def _add_tag(client: AsyncClient, entity_id: str, tag: str) -> None:
    resp = await client.post(f"/entities/{entity_id}/tags", json={"tag": tag})
    assert resp.status_code == 201, resp.text


# ---------------------------------------------------------------------------
# Pattern 1: Pure UUID
# ---------------------------------------------------------------------------


@pytest.mark.anyio
async def test_get_entity_by_uuid(admin_client: AsyncClient):
    eid = await _create_entity(admin_client, canonical_name="uuid test")
    resp = await admin_client.get(f"/entities/{eid}")
    assert resp.status_code == 200
    assert resp.json()["data"]["id"] == eid


# ---------------------------------------------------------------------------
# Pattern 2: PROJECT_ID@UUID (scoped UUID)
# ---------------------------------------------------------------------------


@pytest.mark.anyio
async def test_get_entity_scoped_uuid_match(admin_client: AsyncClient):
    eid = await _create_entity(admin_client, canonical_name="scoped uuid", project_id="proj_a")
    ref = f"proj_a@{eid}"
    resp = await admin_client.get(f"/entities/{ref}")
    assert resp.status_code == 200
    assert resp.json()["data"]["id"] == eid


@pytest.mark.anyio
async def test_get_entity_scoped_uuid_project_mismatch(admin_client: AsyncClient):
    eid = await _create_entity(admin_client, canonical_name="mismatch test", project_id="proj_a")
    ref = f"proj_b@{eid}"
    resp = await admin_client.get(f"/entities/{ref}")
    assert resp.status_code == 404
    assert resp.json()["error"]["code"] == "PROJECT_SCOPE_MISMATCH"


# ---------------------------------------------------------------------------
# Pattern 3: PROJECT_ID@TAG (scoped tag)
# ---------------------------------------------------------------------------


@pytest.mark.anyio
async def test_get_entity_scoped_tag_single_match(admin_client: AsyncClient):
    eid = await _create_entity(admin_client, canonical_name="tag test", project_id="proj_t")
    await _add_tag(admin_client, eid, "auth")
    ref = "proj_t@auth"
    resp = await admin_client.get(f"/entities/{ref}")
    assert resp.status_code == 200
    assert resp.json()["data"]["id"] == eid


@pytest.mark.anyio
async def test_get_entity_scoped_tag_ambiguous(admin_client: AsyncClient):
    eid1 = await _create_entity(admin_client, canonical_name="ambiguous 1", project_id="proj_amb")
    eid2 = await _create_entity(admin_client, canonical_name="ambiguous 2", project_id="proj_amb")
    await _add_tag(admin_client, eid1, "shared_tag")
    await _add_tag(admin_client, eid2, "shared_tag")
    ref = "proj_amb@shared_tag"
    resp = await admin_client.get(f"/entities/{ref}")
    assert resp.status_code == 422
    assert resp.json()["error"]["code"] == "AMBIGUOUS_TAG_REF"
    assert "matched_ids" in resp.json()["error"]["details"]


@pytest.mark.anyio
async def test_get_entity_scoped_tag_missing(admin_client: AsyncClient):
    ref = "proj_none@nonexistent_tag"
    resp = await admin_client.get(f"/entities/{ref}")
    assert resp.status_code == 404
    assert resp.json()["error"]["code"] == "ENTITY_NOT_FOUND"


# ---------------------------------------------------------------------------
# Invalid format
# ---------------------------------------------------------------------------


@pytest.mark.anyio
async def test_get_entity_invalid_format(admin_client: AsyncClient):
    resp = await admin_client.get("/entities/@@invalid@@")
    assert resp.status_code == 422
    assert resp.json()["error"]["code"] == "INVALID_REF_FORMAT"


@pytest.mark.anyio
async def test_get_entity_plain_string_invalid(admin_client: AsyncClient):
    resp = await admin_client.get("/entities/not-a-uuid-at-all")
    assert resp.status_code == 422
    assert resp.json()["error"]["code"] == "INVALID_REF_FORMAT"


# ---------------------------------------------------------------------------
# context-bundle with mixed ref patterns
# ---------------------------------------------------------------------------


@pytest.mark.anyio
async def test_context_bundle_mixed_refs(admin_client: AsyncClient):
    eid1 = await _create_entity(admin_client, canonical_name="bundle 1", project_id="proj_b")
    eid2 = await _create_entity(admin_client, canonical_name="bundle 2", project_id="proj_b")
    await _add_tag(admin_client, eid2, "bundle_tag")

    resp = await admin_client.post("/context-bundle", json={
        "root_ids": [eid1, f"proj_b@{eid2}", "proj_b@bundle_tag"],
        "max_depth": 0,
    })
    assert resp.status_code == 200
    data = resp.json()["data"]
    root_ids_returned = {r["id"] for r in data["roots"]}
    assert eid1 in root_ids_returned
    assert eid2 in root_ids_returned


# ---------------------------------------------------------------------------
# validate-references with mixed ref patterns
# ---------------------------------------------------------------------------


@pytest.mark.anyio
async def test_validate_references_mixed_patterns(admin_client: AsyncClient):
    eid = await _create_entity(admin_client, canonical_name="validate test", project_id="proj_v")
    await _add_tag(admin_client, eid, "vtag")

    resp = await admin_client.post("/validate-references", json={
        "references": [
            eid,                         # Pattern 1: UUID
            f"proj_v@{eid}",             # Pattern 2: PROJECT_ID@UUID
            "proj_v@vtag",               # Pattern 3: PROJECT_ID@TAG single match
            "proj_v@nonexistent_tag",    # Pattern 3: missing
        ]
    })
    assert resp.status_code == 200
    data = resp.json()["data"]
    resolved_inputs = {r["input"] for r in data["resolved"]}
    assert eid in resolved_inputs
    assert f"proj_v@{eid}" in resolved_inputs
    assert "proj_v@vtag" in resolved_inputs
    assert "proj_v@nonexistent_tag" in data["missing"]
