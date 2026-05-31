"""Tests for GET /entities/{id}/history/{rev_a}/compare/{rev_b}."""
from __future__ import annotations

import pytest
from httpx import AsyncClient


async def _make_entity_with_history(admin_client: AsyncClient) -> str:
    resp = await admin_client.post(
        "/entities",
        json={"type": "FEATURE", "canonical_name": "초기 이름", "description": "초기 설명", "status": "candidate"},
    )
    assert resp.status_code == 201
    eid = resp.json()["data"]["id"]

    await admin_client.patch(f"/entities/{eid}", json={"canonical_name": "변경된 이름"})
    await admin_client.patch(f"/entities/{eid}", json={"status": "active", "change_reason": "승인"})
    return eid


@pytest.mark.asyncio
async def test_compare_returns_diff(admin_client: AsyncClient):
    eid = await _make_entity_with_history(admin_client)

    resp = await admin_client.get(f"/entities/{eid}/history/1/compare/2")
    assert resp.status_code == 200
    data = resp.json()["data"]

    assert data["entity_id"] == eid
    assert data["rev_a"]["revision_no"] == 1
    assert data["rev_b"]["revision_no"] == 2

    diff = data["diff"]
    assert diff["canonical_name"]["before"] == "초기 이름"
    assert diff["canonical_name"]["after"] == "변경된 이름"
    assert diff["canonical_name"]["changed"] is True


@pytest.mark.asyncio
async def test_compare_unchanged_fields_marked_false(admin_client: AsyncClient):
    eid = await _make_entity_with_history(admin_client)

    resp = await admin_client.get(f"/entities/{eid}/history/1/compare/2")
    assert resp.status_code == 200
    diff = resp.json()["data"]["diff"]

    assert diff["status"]["changed"] is False
    assert diff["status"]["before"] == "candidate"
    assert diff["status"]["after"] == "candidate"


@pytest.mark.asyncio
async def test_compare_status_change(admin_client: AsyncClient):
    eid = await _make_entity_with_history(admin_client)

    resp = await admin_client.get(f"/entities/{eid}/history/2/compare/3")
    assert resp.status_code == 200
    diff = resp.json()["data"]["diff"]

    assert diff["status"]["before"] == "candidate"
    assert diff["status"]["after"] == "active"
    assert diff["status"]["changed"] is True


@pytest.mark.asyncio
async def test_compare_same_revision_shows_no_changes(admin_client: AsyncClient):
    eid = await _make_entity_with_history(admin_client)

    resp = await admin_client.get(f"/entities/{eid}/history/1/compare/1")
    assert resp.status_code == 200
    diff = resp.json()["data"]["diff"]

    assert all(not v["changed"] for v in diff.values())


@pytest.mark.asyncio
async def test_compare_nonexistent_revision_returns_404(admin_client: AsyncClient):
    eid = await _make_entity_with_history(admin_client)

    resp = await admin_client.get(f"/entities/{eid}/history/1/compare/99")
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_compare_nonexistent_entity_returns_404(client: AsyncClient):
    fake_id = "00000000-0000-0000-0000-000000000001"
    resp = await client.get(f"/entities/{fake_id}/history/1/compare/2")
    assert resp.status_code == 404
