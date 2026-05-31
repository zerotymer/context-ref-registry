"""Tests for POST /entities/batch endpoint."""
from __future__ import annotations

import uuid

import pytest
from httpx import AsyncClient


def _entity_payload(canonical_name: str, project_id: str | None = None, entity_id: str | None = None) -> dict:
    payload: dict = {
        "type": "FEATURE",
        "canonical_name": canonical_name,
        "status": "active",
    }
    if project_id:
        payload["project_id"] = project_id
    if entity_id:
        payload["id"] = entity_id
    return payload


@pytest.mark.anyio
async def test_batch_create_all_success(admin_client: AsyncClient):
    resp = await admin_client.post("/entities/batch", json={
        "entities": [
            _entity_payload("batch entity 1"),
            _entity_payload("batch entity 2"),
        ]
    })
    assert resp.status_code == 207
    data = resp.json()["data"]
    assert data["total"] == 2
    assert data["created"] == 2
    assert data["failed"] == 0
    for item in data["items"]:
        assert item["ok"] is True
        assert item["id"] is not None


@pytest.mark.anyio
async def test_batch_create_partial_failure(admin_client: AsyncClient):
    fixed_id = str(uuid.uuid4())
    # Create once to reserve the ID
    resp1 = await admin_client.post("/entities/batch", json={
        "entities": [_entity_payload("first", entity_id=fixed_id)]
    })
    assert resp1.status_code == 207
    assert resp1.json()["data"]["created"] == 1

    # Second batch: same ID (duplicate) + a new valid one
    resp2 = await admin_client.post("/entities/batch", json={
        "entities": [
            _entity_payload("duplicate", entity_id=fixed_id),
            _entity_payload("valid new entity"),
        ]
    })
    assert resp2.status_code == 207
    data = resp2.json()["data"]
    assert data["total"] == 2
    # One should fail, one should succeed
    assert data["failed"] == 1
    assert data["created"] == 1
    failed = [i for i in data["items"] if not i["ok"]]
    assert len(failed) == 1
    assert failed[0]["error_code"] is not None


@pytest.mark.anyio
async def test_batch_create_over_limit(admin_client: AsyncClient):
    entities = [_entity_payload(f"entity {i}") for i in range(101)]
    resp = await admin_client.post("/entities/batch", json={"entities": entities})
    assert resp.status_code == 422


@pytest.mark.anyio
async def test_batch_create_empty_list(admin_client: AsyncClient):
    resp = await admin_client.post("/entities/batch", json={"entities": []})
    assert resp.status_code == 422


@pytest.mark.anyio
async def test_batch_create_returns_ids(admin_client: AsyncClient):
    resp = await admin_client.post("/entities/batch", json={
        "entities": [_entity_payload("check id entity")]
    })
    assert resp.status_code == 207
    item = resp.json()["data"]["items"][0]
    assert item["ok"] is True
    # Verify the returned ID is a valid UUID and the entity actually exists
    eid = item["id"]
    get_resp = await admin_client.get(f"/entities/{eid}")
    assert get_resp.status_code == 200
    assert get_resp.json()["data"]["id"] == eid


@pytest.mark.anyio
async def test_batch_create_index_matches_order(admin_client: AsyncClient):
    resp = await admin_client.post("/entities/batch", json={
        "entities": [
            _entity_payload("first item"),
            _entity_payload("second item"),
            _entity_payload("third item"),
        ]
    })
    assert resp.status_code == 207
    items = resp.json()["data"]["items"]
    for i, item in enumerate(items):
        assert item["index"] == i
