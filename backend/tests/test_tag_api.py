"""Tests for entity tag feature (Step A)."""
from __future__ import annotations

import pytest
from httpx import AsyncClient


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

async def _create_entity(client: AsyncClient, **kwargs) -> str:
    payload = {
        "type": "FEATURE",
        "canonical_name": kwargs.get("canonical_name", "테스트 기능"),
        **{k: v for k, v in kwargs.items() if k != "canonical_name"},
    }
    resp = await client.post("/entities", json=payload)
    assert resp.status_code == 201, resp.text
    return resp.json()["data"]["id"]


# ---------------------------------------------------------------------------
# A-9: Tag tests
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_create_entity_with_tags(client: AsyncClient):
    eid = await _create_entity(client, canonical_name="태그 있는 기능", tags=["project:frontend", "team:platform"])
    resp = await client.get(f"/entities/{eid}")
    assert resp.status_code == 200
    data = resp.json()["data"]
    assert set(data["tags"]) == {"project:frontend", "team:platform"}


@pytest.mark.asyncio
async def test_create_entity_without_tags(client: AsyncClient):
    eid = await _create_entity(client, canonical_name="태그 없는 기능")
    resp = await client.get(f"/entities/{eid}")
    assert resp.status_code == 200
    assert resp.json()["data"]["tags"] == []


@pytest.mark.asyncio
async def test_patch_replaces_tags(client: AsyncClient):
    eid = await _create_entity(client, tags=["v1", "old"])
    resp = await client.patch(f"/entities/{eid}", json={"tags": ["v2", "new"]})
    assert resp.status_code == 200
    assert set(resp.json()["data"]["tags"]) == {"v2", "new"}

    # 기존 태그 제거 확인
    resp2 = await client.get(f"/entities/{eid}")
    assert "old" not in resp2.json()["data"]["tags"]


@pytest.mark.asyncio
async def test_patch_tags_none_keeps_existing(client: AsyncClient):
    eid = await _create_entity(client, tags=["keep-me"])
    resp = await client.patch(f"/entities/{eid}", json={"canonical_name": "수정된 이름"})
    assert resp.status_code == 200
    assert "keep-me" in resp.json()["data"]["tags"]


@pytest.mark.asyncio
async def test_patch_tags_empty_list_removes_all(client: AsyncClient):
    eid = await _create_entity(client, tags=["to-remove"])
    resp = await client.patch(f"/entities/{eid}", json={"tags": []})
    assert resp.status_code == 200
    assert resp.json()["data"]["tags"] == []


@pytest.mark.asyncio
async def test_get_entity_tags_endpoint(client: AsyncClient):
    eid = await _create_entity(client, tags=["a", "b", "c"])
    resp = await client.get(f"/entities/{eid}/tags")
    assert resp.status_code == 200
    assert set(resp.json()["data"]) == {"a", "b", "c"}


@pytest.mark.asyncio
async def test_add_tag_individually(client: AsyncClient):
    eid = await _create_entity(client, tags=["existing"])
    resp = await client.post(f"/entities/{eid}/tags", json={"tag": "new-tag"})
    assert resp.status_code == 201
    assert "new-tag" in resp.json()["data"]
    assert "existing" in resp.json()["data"]


@pytest.mark.asyncio
async def test_add_duplicate_tag_returns_409(client: AsyncClient):
    eid = await _create_entity(client, tags=["dup"])
    resp = await client.post(f"/entities/{eid}/tags", json={"tag": "dup"})
    assert resp.status_code == 409


@pytest.mark.asyncio
async def test_remove_tag(client: AsyncClient):
    eid = await _create_entity(client, tags=["to-del", "keep"])
    resp = await client.delete(f"/entities/{eid}/tags/to-del")
    assert resp.status_code == 200
    assert resp.json()["data"]["removed"] == "to-del"

    tags = (await client.get(f"/entities/{eid}/tags")).json()["data"]
    assert "to-del" not in tags
    assert "keep" in tags


@pytest.mark.asyncio
async def test_remove_nonexistent_tag_returns_404(client: AsyncClient):
    eid = await _create_entity(client)
    resp = await client.delete(f"/entities/{eid}/tags/ghost")
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_list_all_tags(client: AsyncClient):
    await _create_entity(client, canonical_name="기능 A", tags=["shared", "only-a"])
    await _create_entity(client, canonical_name="기능 B", tags=["shared", "only-b"])

    resp = await client.get("/tags")
    assert resp.status_code == 200
    tags = {item["tag"]: item["count"] for item in resp.json()["data"]}
    assert tags["shared"] == 2
    assert tags["only-a"] == 1
    assert tags["only-b"] == 1


@pytest.mark.asyncio
async def test_list_entities_filter_by_single_tag(client: AsyncClient):
    eid1 = await _create_entity(client, canonical_name="기능 1", tags=["project:frontend"])
    eid2 = await _create_entity(client, canonical_name="기능 2", tags=["project:backend"])

    resp = await client.get("/entities", params={"tags": "project:frontend"})
    assert resp.status_code == 200
    ids = [e["id"] for e in resp.json()["data"]["items"]]
    assert eid1 in ids
    assert eid2 not in ids


@pytest.mark.asyncio
async def test_list_entities_filter_by_multiple_tags_and_logic(client: AsyncClient):
    eid_both = await _create_entity(client, canonical_name="둘 다 있음", tags=["tagA", "tagB"])
    eid_only_a = await _create_entity(client, canonical_name="A만", tags=["tagA"])

    resp = await client.get("/entities", params=[("tags", "tagA"), ("tags", "tagB")])
    assert resp.status_code == 200
    ids = [e["id"] for e in resp.json()["data"]["items"]]
    assert eid_both in ids
    assert eid_only_a not in ids


@pytest.mark.asyncio
async def test_search_with_tag_filter(client: AsyncClient):
    eid1 = await _create_entity(client, canonical_name="검색 대상 A", tags=["findme"])
    eid2 = await _create_entity(client, canonical_name="검색 대상 B", tags=["other"])

    resp = await client.get("/search", params={"q": "검색 대상", "tags": "findme"})
    assert resp.status_code == 200
    ids = [e["id"] for e in resp.json()["data"]]
    assert eid1 in ids
    assert eid2 not in ids


@pytest.mark.asyncio
async def test_batch_ingest_with_tags(client: AsyncClient):
    resp = await client.post("/ingest/batch", json={
        "source": {"type": "test", "uri": "file://test-tags", "name": "tag test"},
        "entities": [{
            "type": "FEATURE",
            "canonical_name": "배치 태그 기능",
            "tags": ["batch-tag", "project:test"],
        }],
        "relations": [],
    })
    assert resp.status_code == 200
    source_ref_id = resp.json()["data"]["source_ref_id"]

    # 생성된 entity 검색 후 태그 확인
    search_resp = await client.get("/search", params={"q": "배치 태그 기능"})
    assert search_resp.status_code == 200
    results = search_resp.json()["data"]
    assert len(results) == 1
    entity_id = results[0]["id"]

    tag_resp = await client.get(f"/entities/{entity_id}/tags")
    assert set(tag_resp.json()["data"]) == {"batch-tag", "project:test"}


@pytest.mark.asyncio
async def test_batch_ingest_idempotent_tags(client: AsyncClient):
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
    await client.post("/ingest/batch", json=payload)
    await client.post("/ingest/batch", json=payload)

    search_resp = await client.get("/search", params={"q": "멱등 태그 기능"})
    entity_id = search_resp.json()["data"][0]["id"]
    tag_resp = await client.get(f"/entities/{entity_id}/tags")
    assert tag_resp.json()["data"].count("stable-tag") == 1
