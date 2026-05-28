"""Tests for entity history feature (Step B)."""
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


async def _get_history(client: AsyncClient, entity_id: str) -> list[dict]:
    resp = await client.get(f"/entities/{entity_id}/history")
    assert resp.status_code == 200
    return resp.json()["data"]["items"]


# ---------------------------------------------------------------------------
# B-8: History tests
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_create_entity_generates_revision_1(client: AsyncClient):
    eid = await _create_entity(client, canonical_name="히스토리 기능")
    history = await _get_history(client, eid)
    assert len(history) == 1
    assert history[0]["revision_no"] == 1
    assert history[0]["change_type"] == "create"


@pytest.mark.asyncio
async def test_update_increments_revision_no(client: AsyncClient):
    eid = await _create_entity(client, canonical_name="업데이트 기능")
    await client.patch(f"/entities/{eid}", json={"canonical_name": "업데이트된 기능"})
    history = await _get_history(client, eid)
    assert len(history) == 2
    rev_nos = sorted(h["revision_no"] for h in history)
    assert rev_nos == [1, 2]


@pytest.mark.asyncio
async def test_update_snapshot_is_before_image(client: AsyncClient):
    eid = await _create_entity(client, canonical_name="원래 이름")
    await client.patch(f"/entities/{eid}", json={"canonical_name": "바뀐 이름"})

    history = await _get_history(client, eid)
    # 최신순이므로 history[0]이 revision_no=2 (update)
    update_entry = next(h for h in history if h["revision_no"] == 2)
    assert update_entry["snapshot"]["canonical_name"] == "원래 이름"
    assert update_entry["change_type"] == "update"
    assert update_entry["changed_fields"]["canonical_name"]["before"] == "원래 이름"
    assert update_entry["changed_fields"]["canonical_name"]["after"] == "바뀐 이름"


@pytest.mark.asyncio
async def test_status_change_type(client: AsyncClient):
    eid = await _create_entity(client)
    await client.patch(f"/entities/{eid}", json={"status": "active"})
    history = await _get_history(client, eid)
    update_entry = next(h for h in history if h["revision_no"] == 2)
    assert update_entry["change_type"] == "status_change"


@pytest.mark.asyncio
async def test_deprecate_change_type(client: AsyncClient):
    eid = await _create_entity(client)
    await client.patch(f"/entities/{eid}", json={"status": "deprecated", "deprecation_reason": "obsolete"})
    history = await _get_history(client, eid)
    update_entry = next(h for h in history if h["revision_no"] == 2)
    assert update_entry["change_type"] == "deprecate"


@pytest.mark.asyncio
async def test_history_list_descending_order(client: AsyncClient):
    eid = await _create_entity(client, canonical_name="정렬 테스트")
    await client.patch(f"/entities/{eid}", json={"canonical_name": "수정 1"})
    await client.patch(f"/entities/{eid}", json={"canonical_name": "수정 2"})

    history = await _get_history(client, eid)
    assert len(history) == 3
    rev_nos = [h["revision_no"] for h in history]
    assert rev_nos == sorted(rev_nos, reverse=True)


@pytest.mark.asyncio
async def test_get_specific_revision(client: AsyncClient):
    eid = await _create_entity(client, canonical_name="리비전 조회")
    await client.patch(f"/entities/{eid}", json={"canonical_name": "변경됨"})

    resp = await client.get(f"/entities/{eid}/history/1")
    assert resp.status_code == 200
    data = resp.json()["data"]
    assert data["revision_no"] == 1
    assert data["change_type"] == "create"


@pytest.mark.asyncio
async def test_get_nonexistent_revision_returns_404(client: AsyncClient):
    eid = await _create_entity(client)
    resp = await client.get(f"/entities/{eid}/history/99")
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_changed_by_header_saved(client: AsyncClient):
    resp = await client.post(
        "/entities",
        json={"type": "FEATURE", "canonical_name": "에이전트 기록"},
        headers={"X-Changed-By": "agent-codex-v1"},
    )
    assert resp.status_code == 201
    eid = resp.json()["data"]["id"]
    history = await _get_history(client, eid)
    assert history[0]["changed_by"] == "agent-codex-v1"


@pytest.mark.asyncio
async def test_change_reason_saved(client: AsyncClient):
    eid = await _create_entity(client)
    await client.patch(
        f"/entities/{eid}",
        json={"status": "active", "change_reason": "QA 완료 후 승인"},
    )
    history = await _get_history(client, eid)
    update_entry = next(h for h in history if h["revision_no"] == 2)
    assert update_entry["change_reason"] == "QA 완료 후 승인"


@pytest.mark.asyncio
async def test_batch_ingest_creates_history(client: AsyncClient):
    resp = await client.post("/ingest/batch", json={
        "source": {"type": "test", "uri": "file://hist-ingest", "name": "hist-source"},
        "entities": [{"type": "FEATURE", "canonical_name": "인제스트 히스토리"}],
        "relations": [],
    })
    assert resp.status_code == 200

    search_resp = await client.get("/search", params={"q": "인제스트 히스토리"})
    eid = search_resp.json()["data"][0]["id"]
    history = await _get_history(client, eid)
    assert len(history) == 1
    assert history[0]["change_type"] == "create"
    assert history[0]["changed_by"] == "hist-source"


@pytest.mark.asyncio
async def test_batch_ingest_update_creates_new_revision(client: AsyncClient):
    payload_base = {
        "source": {"type": "test", "uri": "file://hist-re-ingest", "name": "re-ingest-source"},
        "entities": [{"type": "FEATURE", "canonical_name": "재인제스트 기능"}],
        "relations": [],
    }
    await client.post("/ingest/batch", json=payload_base)
    search_resp = await client.get("/search", params={"q": "재인제스트 기능"})
    eid = search_resp.json()["data"][0]["id"]

    payload_update = {
        "source": {"type": "test", "uri": "file://hist-re-ingest", "name": "re-ingest-source"},
        "entities": [{"id": eid, "type": "FEATURE", "canonical_name": "재인제스트 기능 v2"}],
        "relations": [],
    }
    await client.post("/ingest/batch", json=payload_update)

    history = await _get_history(client, eid)
    assert len(history) == 2
    assert any(h["change_type"] == "update" for h in history)


@pytest.mark.asyncio
async def test_history_total_count(client: AsyncClient):
    eid = await _create_entity(client)
    for i in range(3):
        await client.patch(f"/entities/{eid}", json={"canonical_name": f"변경 {i}"})

    resp = await client.get(f"/entities/{eid}/history")
    assert resp.json()["data"]["total"] == 4  # create + 3 updates


@pytest.mark.asyncio
async def test_history_pagination(client: AsyncClient):
    eid = await _create_entity(client)
    for i in range(4):
        await client.patch(f"/entities/{eid}", json={"canonical_name": f"페이징 {i}"})

    resp = await client.get(f"/entities/{eid}/history", params={"limit": 2, "offset": 0})
    assert resp.status_code == 200
    data = resp.json()["data"]
    assert len(data["items"]) == 2
    assert data["total"] == 5


@pytest.mark.asyncio
async def test_history_for_nonexistent_entity_returns_404(client: AsyncClient):
    fake_id = "00000000-0000-0000-0000-000000000001"
    resp = await client.get(f"/entities/{fake_id}/history")
    assert resp.status_code == 404
