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
async def test_batch_ingest_unauthenticated_returns_401(client: AsyncClient):
    payload = {"source": SAMPLE_SOURCE, "entities": [], "relations": []}
    res = await client.post("/ingest/batch", json=payload)
    assert res.status_code == 401


@pytest.mark.asyncio
async def test_batch_ingest_ok(admin_client: AsyncClient):
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

    res = await admin_client.post("/ingest/batch", json=payload)
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
async def test_batch_ingest_alias_count(admin_client: AsyncClient):
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
    res = await admin_client.post("/ingest/batch", json=payload)
    assert res.status_code == 200
    data = res.json()["data"]
    assert data["created"]["aliases"] == 3


@pytest.mark.asyncio
async def test_batch_ingest_alias_dedup(admin_client: AsyncClient):
    """Same alias re-ingested should be skipped (not duplicated)."""
    payload = {
        "source": SAMPLE_SOURCE,
        "entities": [
            _make_entity(ENTITY_A_ID, "UI_AREA", aliases={"ko": ["검색 영역"]})
        ],
        "relations": [],
    }
    # First ingest
    res1 = await admin_client.post("/ingest/batch", json=payload)
    assert res1.status_code == 200
    assert res1.json()["data"]["created"]["aliases"] == 1

    # Second ingest — same alias should be skipped
    res2 = await admin_client.post("/ingest/batch", json=payload)
    assert res2.status_code == 200
    assert res2.json()["data"]["created"]["aliases"] == 0


@pytest.mark.asyncio
async def test_batch_ingest_entity_upsert(admin_client: AsyncClient):
    """Existing entity should be updated, not duplicated."""
    payload1 = {
        "source": SAMPLE_SOURCE,
        "entities": [_make_entity(ENTITY_A_ID, "UI_AREA", canonical_name="원래 이름")],
        "relations": [],
    }
    res1 = await admin_client.post("/ingest/batch", json=payload1)
    assert res1.json()["data"]["created"]["entities"] == 1

    payload2 = {
        "source": SAMPLE_SOURCE,
        "entities": [_make_entity(ENTITY_A_ID, "UI_AREA", canonical_name="새 이름")],
        "relations": [],
    }
    res2 = await admin_client.post("/ingest/batch", json=payload2)
    assert res2.status_code == 200
    data2 = res2.json()["data"]
    assert data2["created"]["entities"] == 0
    assert data2["updated"]["entities"] == 1


@pytest.mark.asyncio
async def test_batch_ingest_type_change_forbidden(admin_client: AsyncClient):
    """Changing entity type should return error."""
    payload1 = {
        "source": SAMPLE_SOURCE,
        "entities": [_make_entity(ENTITY_A_ID, "UI_AREA")],
        "relations": [],
    }
    await admin_client.post("/ingest/batch", json=payload1)

    payload2 = {
        "source": SAMPLE_SOURCE,
        "entities": [_make_entity(ENTITY_A_ID, "FEATURE")],
        "relations": [],
    }
    res = await admin_client.post("/ingest/batch", json=payload2)
    assert res.status_code == 400
    body = res.json()
    assert body["ok"] is False
    assert body["error"]["code"] == "TYPE_CHANGE_FORBIDDEN"


@pytest.mark.asyncio
async def test_batch_ingest_relation_missing_target(admin_client: AsyncClient):
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
    res = await admin_client.post("/ingest/batch", json=payload)
    assert res.status_code == 400
    body = res.json()
    assert body["ok"] is False
    assert body["error"]["code"] == "INVALID_RELATION_TARGET"


@pytest.mark.asyncio
async def test_batch_ingest_relation_within_batch(admin_client: AsyncClient):
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
    res = await admin_client.post("/ingest/batch", json=payload)
    assert res.status_code == 200
    data = res.json()["data"]
    assert data["created"]["entities"] == 2
    assert data["created"]["relations"] == 1


@pytest.mark.asyncio
async def test_batch_ingest_relation_to_existing_db_entity(admin_client: AsyncClient):
    """Relation target can be an entity that already exists in the DB."""
    # Pre-create entity B via regular API
    res_b = await admin_client.post(
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
    res = await admin_client.post("/ingest/batch", json=payload)
    assert res.status_code == 200
    data = res.json()["data"]
    assert data["created"]["relations"] == 1


@pytest.mark.asyncio
async def test_batch_ingest_no_entities(admin_client: AsyncClient):
    """Empty entity list should succeed."""
    payload = {"source": SAMPLE_SOURCE, "entities": [], "relations": []}
    res = await admin_client.post("/ingest/batch", json=payload)
    assert res.status_code == 200
    data = res.json()["data"]
    assert data["created"]["entities"] == 0


@pytest.mark.asyncio
async def test_batch_ingest_source_ref_dedup(admin_client: AsyncClient):
    """Same URI ingested twice should reuse the same source_ref."""
    payload = {
        "source": SAMPLE_SOURCE,
        "entities": [_make_entity(ENTITY_A_ID, "UI_AREA")],
        "relations": [],
    }
    res1 = await admin_client.post("/ingest/batch", json=payload)
    res2 = await admin_client.post("/ingest/batch", json=payload)
    assert res1.json()["data"]["source_ref_id"] == res2.json()["data"]["source_ref_id"]


ISSUE_ENTITY_ID = "2e4f7a1b-8c3d-4e5f-9a0b-1c2d3e4f5a6b"


@pytest.mark.asyncio
async def test_batch_ingest_returns_entity_refs(admin_client: AsyncClient):
    """Response entities[] maps input index → stored id, operation, aliases."""
    payload = {
        "source": SAMPLE_SOURCE,
        "entities": [
            _make_entity(
                ENTITY_A_ID,
                "UI_AREA",
                canonical_name="검색 영역",
                aliases={"ko": ["검색 영역"], "en": ["Search Area"]},
            ),
            _make_entity(ENTITY_B_ID, "FEATURE", canonical_name="사용자 검색"),
        ],
        "relations": [],
    }
    res = await admin_client.post("/ingest/batch", json=payload)
    assert res.status_code == 200
    refs = res.json()["data"]["entities"]
    assert len(refs) == 2

    a, b = refs[0], refs[1]
    assert a["index"] == 0
    assert a["entity_id"] == ENTITY_A_ID
    assert a["canonical_name"] == "검색 영역"
    assert a["operation"] == "created"
    assert a["aliases"] == {"ko": ["검색 영역"], "en": ["Search Area"]}
    assert b["index"] == 1
    assert b["entity_id"] == ENTITY_B_ID


@pytest.mark.asyncio
async def test_batch_ingest_server_assigned_id_is_resolvable(admin_client: AsyncClient):
    """id-less input → server assigns UUID; returned entity_id is fetchable."""
    payload = {
        "source": SAMPLE_SOURCE,
        "entities": [
            {
                "type": "UI_AREA",
                "canonical_name": "신규 영역",
                "aliases": {},
                "contexts": [],
            }
        ],
        "relations": [],
    }
    res = await admin_client.post("/ingest/batch", json=payload)
    assert res.status_code == 200
    refs = res.json()["data"]["entities"]
    assert len(refs) == 1
    entity_id = refs[0]["entity_id"]

    # Re-fetch using the returned id — no re-search needed
    got = await admin_client.get(f"/entities/{entity_id}")
    assert got.status_code == 200
    assert got.json()["data"]["canonical_name"] == "신규 영역"


@pytest.mark.asyncio
async def test_batch_ingest_ref_operation_updated(admin_client: AsyncClient):
    """Re-ingesting an existing entity reports operation=updated."""
    payload = {
        "source": SAMPLE_SOURCE,
        "entities": [_make_entity(ENTITY_A_ID, "UI_AREA")],
        "relations": [],
    }
    res1 = await admin_client.post("/ingest/batch", json=payload)
    assert res1.json()["data"]["entities"][0]["operation"] == "created"

    res2 = await admin_client.post("/ingest/batch", json=payload)
    assert res2.json()["data"]["entities"][0]["operation"] == "updated"


@pytest.mark.asyncio
async def test_batch_ingest_issue_type(admin_client: AsyncClient):
    """ISSUE entity type should be ingested successfully."""
    payload = {
        "source": SAMPLE_SOURCE,
        "entities": [
            _make_entity(
                ISSUE_ENTITY_ID,
                "ISSUE",
                canonical_name="로그인 버튼 비활성화 버그",
                contexts=[{"context_type": "summary", "body": "특정 조건에서 버튼 비활성화", "language": "ko"}],
            )
        ],
        "relations": [],
    }
    res = await admin_client.post("/ingest/batch", json=payload)
    assert res.status_code == 200
    body = res.json()
    assert body["ok"] is True
    assert body["data"]["created"]["entities"] == 1
