"""Tests for entity tag feature (Step A), updated for auth in Step 2-2."""
from __future__ import annotations

import pytest
from httpx import AsyncClient


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

async def _create_entity(admin_client: AsyncClient, **kwargs) -> str:
    payload = {
        "type": "FEATURE",
        "canonical_name": kwargs.get("canonical_name", "테스트 기능"),
        **{k: v for k, v in kwargs.items() if k != "canonical_name"},
    }
    resp = await admin_client.post("/entities", json=payload)
    assert resp.status_code == 201, resp.text
    return resp.json()["data"]["id"]


# ---------------------------------------------------------------------------
# A-9: Tag tests
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_create_entity_with_tags(admin_client: AsyncClient):
    eid = await _create_entity(admin_client, canonical_name="태그 있는 기능", tags=["project:frontend", "team:platform"])
    resp = await admin_client.get(f"/entities/{eid}")
    assert resp.status_code == 200
    data = resp.json()["data"]
    assert set(data["tags"]) == {"project:frontend", "team:platform"}


@pytest.mark.asyncio
async def test_create_entity_without_tags(admin_client: AsyncClient):
    eid = await _create_entity(admin_client, canonical_name="태그 없는 기능")
    resp = await admin_client.get(f"/entities/{eid}")
    assert resp.status_code == 200
    assert resp.json()["data"]["tags"] == []


@pytest.mark.asyncio
async def test_patch_replaces_tags(admin_client: AsyncClient):
    eid = await _create_entity(admin_client, tags=["v1", "old"])
    resp = await admin_client.patch(f"/entities/{eid}", json={"tags": ["v2", "new"]})
    assert resp.status_code == 200
    assert set(resp.json()["data"]["tags"]) == {"v2", "new"}

    resp2 = await admin_client.get(f"/entities/{eid}")
    assert "old" not in resp2.json()["data"]["tags"]


@pytest.mark.asyncio
async def test_patch_tags_none_keeps_existing(admin_client: AsyncClient):
    eid = await _create_entity(admin_client, tags=["keep-me"])
    resp = await admin_client.patch(f"/entities/{eid}", json={"canonical_name": "수정된 이름"})
    assert resp.status_code == 200
    assert "keep-me" in resp.json()["data"]["tags"]


@pytest.mark.asyncio
async def test_patch_tags_empty_list_removes_all(admin_client: AsyncClient):
    eid = await _create_entity(admin_client, tags=["to-remove"])
    resp = await admin_client.patch(f"/entities/{eid}", json={"tags": []})
    assert resp.status_code == 200
    assert resp.json()["data"]["tags"] == []


@pytest.mark.asyncio
async def test_get_entity_tags_endpoint(admin_client: AsyncClient):
    eid = await _create_entity(admin_client, tags=["a", "b", "c"])
    resp = await admin_client.get(f"/entities/{eid}/tags")
    assert resp.status_code == 200
    assert set(resp.json()["data"]) == {"a", "b", "c"}


@pytest.mark.asyncio
async def test_add_tag_individually(admin_client: AsyncClient):
    eid = await _create_entity(admin_client, tags=["existing"])
    resp = await admin_client.post(f"/entities/{eid}/tags", json={"tag": "new-tag"})
    assert resp.status_code == 201
    assert "new-tag" in resp.json()["data"]
    assert "existing" in resp.json()["data"]


@pytest.mark.asyncio
async def test_add_duplicate_tag_returns_409(admin_client: AsyncClient):
    eid = await _create_entity(admin_client, tags=["dup"])
    resp = await admin_client.post(f"/entities/{eid}/tags", json={"tag": "dup"})
    assert resp.status_code == 409


@pytest.mark.asyncio
async def test_remove_tag(admin_client: AsyncClient):
    eid = await _create_entity(admin_client, tags=["to-del", "keep"])
    resp = await admin_client.delete(f"/entities/{eid}/tags/to-del")
    assert resp.status_code == 200
    assert resp.json()["data"]["removed"] == "to-del"

    tags = (await admin_client.get(f"/entities/{eid}/tags")).json()["data"]
    assert "to-del" not in tags
    assert "keep" in tags


@pytest.mark.asyncio
async def test_remove_nonexistent_tag_returns_404(admin_client: AsyncClient):
    eid = await _create_entity(admin_client)
    resp = await admin_client.delete(f"/entities/{eid}/tags/ghost")
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_list_all_tags(admin_client: AsyncClient):
    await _create_entity(admin_client, canonical_name="기능 A", tags=["shared", "only-a"])
    await _create_entity(admin_client, canonical_name="기능 B", tags=["shared", "only-b"])

    resp = await admin_client.get("/tags")
    assert resp.status_code == 200
    tags = {item["tag"]: item["count"] for item in resp.json()["data"]}
    assert tags["shared"] == 2
    assert tags["only-a"] == 1
    assert tags["only-b"] == 1


@pytest.mark.asyncio
async def test_list_entities_filter_by_single_tag(admin_client: AsyncClient):
    eid1 = await _create_entity(admin_client, canonical_name="기능 1", tags=["project:frontend"])
    eid2 = await _create_entity(admin_client, canonical_name="기능 2", tags=["project:backend"])

    resp = await admin_client.get("/entities", params={"tags": "project:frontend"})
    assert resp.status_code == 200
    ids = [e["id"] for e in resp.json()["data"]["items"]]
    assert eid1 in ids
    assert eid2 not in ids


@pytest.mark.asyncio
async def test_list_entities_filter_by_multiple_tags_and_logic(admin_client: AsyncClient):
    eid_both = await _create_entity(admin_client, canonical_name="둘 다 있음", tags=["tagA", "tagB"])
    eid_only_a = await _create_entity(admin_client, canonical_name="A만", tags=["tagA"])

    resp = await admin_client.get("/entities", params=[("tags", "tagA"), ("tags", "tagB")])
    assert resp.status_code == 200
    ids = [e["id"] for e in resp.json()["data"]["items"]]
    assert eid_both in ids
    assert eid_only_a not in ids


@pytest.mark.asyncio
async def test_search_with_tag_filter(admin_client: AsyncClient):
    eid1 = await _create_entity(admin_client, canonical_name="검색 대상 A", tags=["findme"])
    eid2 = await _create_entity(admin_client, canonical_name="검색 대상 B", tags=["other"])

    resp = await admin_client.get("/search", params={"q": "검색 대상", "tags": "findme"})
    assert resp.status_code == 200
    ids = [e["id"] for e in resp.json()["data"]]
    assert eid1 in ids
    assert eid2 not in ids


@pytest.mark.asyncio
async def test_batch_ingest_with_tags(admin_client: AsyncClient):
    resp = await admin_client.post("/ingest/batch", json={
        "source": {"type": "test", "uri": "file://test-tags", "name": "tag test"},
        "entities": [{
            "type": "FEATURE",
            "canonical_name": "배치 태그 기능",
            "tags": ["batch-tag", "project:test"],
        }],
        "relations": [],
    })
    assert resp.status_code == 200

    search_resp = await admin_client.get("/search", params={"q": "배치 태그 기능"})
    assert search_resp.status_code == 200
    results = search_resp.json()["data"]
    assert len(results) == 1
    entity_id = results[0]["id"]

    tag_resp = await admin_client.get(f"/entities/{entity_id}/tags")
    assert set(tag_resp.json()["data"]) == {"batch-tag", "project:test"}


@pytest.mark.asyncio
async def test_batch_ingest_idempotent_tags(admin_client: AsyncClient):
    """동일 entity를 두 번 ingest해도 tag가 중복되지 않는다."""
    payload = {
        "source": {"type": "test", "uri": "file://idempotent-tags", "name": "tag idempotent"},
        "entities": [{
            "type": "FEATURE",
            "canonical_name": "멱등 태그 기능",
            "tags": ["stable-tag"],
        }],
        "relations": [],
    }
    await admin_client.post("/ingest/batch", json=payload)
    await admin_client.post("/ingest/batch", json=payload)

    search_resp = await admin_client.get("/search", params={"q": "멱등 태그 기능"})
    entity_id = search_resp.json()["data"][0]["id"]
    tag_resp = await admin_client.get(f"/entities/{entity_id}/tags")
    assert tag_resp.json()["data"].count("stable-tag") == 1
