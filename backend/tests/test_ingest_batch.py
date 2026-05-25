"""Batch ingest endpoint tests."""
import pytest
from httpx import AsyncClient

SAMPLE_SOURCE = {
    "type": "screen_spec",
    "name": "test-spec.md",
    "uri": "file://docs/test-spec.md",
    "version": "2026-05-25",
}

ENTITY_A_ID = "0d18b76a-6c0e-45b4-9289-6bdfc2e87e5a"
ENTITY_B_ID = "1c9323e9-46a4-4665-b2d1-c37e4f3b19e0"


def _make_entity(eid: str, etype: str = "UI_AREA", **kwargs) -> dict:
    base = {
        "id": eid,
        "type": etype,
        "canonical_name": f"entity-{eid[:6]}",
        "status": "candidate",
        "confidence": 0.9,
        "aliases": {},
        "contexts": [],
    }
    base.update(kwargs)
    return base


@pytest.mark.asyncio
async def test_batch_ingest_ok(client: AsyncClient):
    payload = {
        "source": SAMPLE_SOURCE,
        "entities": [
            _make_entity(
                ENTITY_A_ID,
                "UI_AREA",
                canonical_name="사용자 검색 조건 영역",
                aliases={"ko": ["검색 영역"], "en": ["Search Area"]},
                contexts=[
                    {"context_type": "summary", "body": "검색 조건 영역", "language": "ko"}
                ],
                metadata={"ui_framework": "react"},
            ),
            _make_entity(
                ENTITY_B_ID,
                "FEATURE",
                canonical_name="사용자 검색",
                aliases={"ko": ["사용자 검색"], "en": ["User Search"]},
            ),
        ],
        "relations": [
            {
                "from_entity_id": ENTITY_A_ID,
                "to_entity_id": ENTITY_B_ID,
                "relation_type": "RELATED_TO",
                "confidence": 0.9,
            }
        ],
    }

    res = await client.post("/ingest/batch", json=payload)
    assert res.status_code == 200
    body = res.json()
    assert body["ok"] is True
    data = body["data"]
    assert data["created"]["entities"] == 2
    assert data["created"]["aliases"] == 4  # A: ko+en=2, B: ko+en=2
    assert data["created"]["contexts"] == 1
    assert data["created"]["relations"] == 1
    assert data["updated"]["entities"] == 0
    assert "source_ref_id" in data


@pytest.mark.asyncio
async def test_batch_ingest_alias_count(client: AsyncClient):
    payload = {
        "source": SAMPLE_SOURCE,
        "entities": [
            _make_entity(
                ENTITY_A_ID,
                "UI_AREA",
                aliases={"ko": ["alias1", "alias2"], "en": ["alias3"]},
            )
        ],
        "relations": [],
    }
    res = await client.post("/ingest/batch", json=payload)
    assert res.status_code == 200
    data = res.json()["data"]
    assert data["created"]["aliases"] == 3


@pytest.mark.asyncio
async def test_batch_ingest_alias_dedup(client: AsyncClient):
    """Same alias re-ingested should be skipped (not duplicated)."""
    payload = {
        "source": SAMPLE_SOURCE,
        "entities": [
            _make_entity(ENTITY_A_ID, "UI_AREA", aliases={"ko": ["검색 영역"]})
        ],
        "relations": [],
    }
    # First ingest
    res1 = await client.post("/ingest/batch", json=payload)
    assert res1.status_code == 200
    assert res1.json()["data"]["created"]["aliases"] == 1

    # Second ingest — same alias should be skipped
    res2 = await client.post("/ingest/batch", json=payload)
    assert res2.status_code == 200
    assert res2.json()["data"]["created"]["aliases"] == 0


@pytest.mark.asyncio
async def test_batch_ingest_entity_upsert(client: AsyncClient):
    """Existing entity should be updated, not duplicated."""
    payload1 = {
        "source": SAMPLE_SOURCE,
        "entities": [_make_entity(ENTITY_A_ID, "UI_AREA", canonical_name="원래 이름")],
        "relations": [],
    }
    res1 = await client.post("/ingest/batch", json=payload1)
    assert res1.json()["data"]["created"]["entities"] == 1

    payload2 = {
        "source": SAMPLE_SOURCE,
        "entities": [_make_entity(ENTITY_A_ID, "UI_AREA", canonical_name="새 이름")],
        "relations": [],
    }
    res2 = await client.post("/ingest/batch", json=payload2)
    assert res2.status_code == 200
    data2 = res2.json()["data"]
    assert data2["created"]["entities"] == 0
    assert data2["updated"]["entities"] == 1


@pytest.mark.asyncio
async def test_batch_ingest_type_change_forbidden(client: AsyncClient):
    """Changing entity type should return error."""
    payload1 = {
        "source": SAMPLE_SOURCE,
        "entities": [_make_entity(ENTITY_A_ID, "UI_AREA")],
        "relations": [],
    }
    await client.post("/ingest/batch", json=payload1)

    payload2 = {
        "source": SAMPLE_SOURCE,
        "entities": [_make_entity(ENTITY_A_ID, "FEATURE")],
        "relations": [],
    }
    res = await client.post("/ingest/batch", json=payload2)
    assert res.status_code == 400
    body = res.json()
    assert body["ok"] is False
    assert body["error"]["code"] == "TYPE_CHANGE_FORBIDDEN"


@pytest.mark.asyncio
async def test_batch_ingest_relation_missing_target(client: AsyncClient):
    """Relation pointing to non-existent entity should fail."""
    missing_id = "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"
    payload = {
        "source": SAMPLE_SOURCE,
        "entities": [_make_entity(ENTITY_A_ID, "UI_AREA")],
        "relations": [
            {
                "from_entity_id": ENTITY_A_ID,
                "to_entity_id": missing_id,
                "relation_type": "RELATED_TO",
            }
        ],
    }
    res = await client.post("/ingest/batch", json=payload)
    assert res.status_code == 400
    body = res.json()
    assert body["ok"] is False
    assert body["error"]["code"] == "INVALID_RELATION_TARGET"


@pytest.mark.asyncio
async def test_batch_ingest_relation_within_batch(client: AsyncClient):
    """Relation between two entities defined in the same batch should succeed."""
    payload = {
        "source": SAMPLE_SOURCE,
        "entities": [
            _make_entity(ENTITY_A_ID, "UI_AREA"),
            _make_entity(ENTITY_B_ID, "FEATURE"),
        ],
        "relations": [
            {
                "from_entity_id": ENTITY_A_ID,
                "to_entity_id": ENTITY_B_ID,
                "relation_type": "CONTAINS",
            }
        ],
    }
    res = await client.post("/ingest/batch", json=payload)
    assert res.status_code == 200
    data = res.json()["data"]
    assert data["created"]["entities"] == 2
    assert data["created"]["relations"] == 1


@pytest.mark.asyncio
async def test_batch_ingest_relation_to_existing_db_entity(client: AsyncClient):
    """Relation target can be an entity that already exists in the DB."""
    # Pre-create entity B via regular API
    res_b = await client.post(
        "/entities",
        json={
            "id": ENTITY_B_ID,
            "type": "FEATURE",
            "canonical_name": "사전 등록 피처",
        },
    )
    assert res_b.status_code == 201

    payload = {
        "source": SAMPLE_SOURCE,
        "entities": [_make_entity(ENTITY_A_ID, "UI_AREA")],
        "relations": [
            {
                "from_entity_id": ENTITY_A_ID,
                "to_entity_id": ENTITY_B_ID,
                "relation_type": "USES",
            }
        ],
    }
    res = await client.post("/ingest/batch", json=payload)
    assert res.status_code == 200
    data = res.json()["data"]
    assert data["created"]["relations"] == 1


@pytest.mark.asyncio
async def test_batch_ingest_no_entities(client: AsyncClient):
    """Empty entity list should succeed."""
    payload = {"source": SAMPLE_SOURCE, "entities": [], "relations": []}
    res = await client.post("/ingest/batch", json=payload)
    assert res.status_code == 200
    data = res.json()["data"]
    assert data["created"]["entities"] == 0


@pytest.mark.asyncio
async def test_batch_ingest_source_ref_dedup(client: AsyncClient):
    """Same URI ingested twice should reuse the same source_ref."""
    payload = {
        "source": SAMPLE_SOURCE,
        "entities": [_make_entity(ENTITY_A_ID, "UI_AREA")],
        "relations": [],
    }
    res1 = await client.post("/ingest/batch", json=payload)
    res2 = await client.post("/ingest/batch", json=payload)
    assert res1.json()["data"]["source_ref_id"] == res2.json()["data"]["source_ref_id"]
