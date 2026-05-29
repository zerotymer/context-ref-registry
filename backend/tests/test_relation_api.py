"""Relation API tests — Step 6, updated for auth in Step 2-2."""
import uuid

from httpx import AsyncClient


async def _create_entity(admin_client: AsyncClient, name: str = "테스트 엔티티", entity_type: str = "FEATURE") -> str:
    resp = await admin_client.post("/entities", json={"type": entity_type, "canonical_name": name})
    assert resp.status_code == 201
    return resp.json()["data"]["id"]


async def _create_relation(
    admin_client: AsyncClient,
    from_id: str,
    to_id: str,
    relation_type: str = "RELATED_TO",
) -> dict:
    resp = await admin_client.post(
        "/relations",
        json={"from_entity_id": from_id, "to_entity_id": to_id, "relation_type": relation_type},
    )
    assert resp.status_code == 201
    return resp.json()["data"]


# ---------------------------------------------------------------------------
# POST /relations
# ---------------------------------------------------------------------------


async def test_create_relation_returns_201(admin_client: AsyncClient):
    from_id = await _create_entity(admin_client, "엔티티 A")
    to_id = await _create_entity(admin_client, "엔티티 B")
    resp = await admin_client.post("/relations", json={
        "from_entity_id": from_id,
        "to_entity_id": to_id,
        "relation_type": "RELATED_TO",
        "description": "A와 B의 관계",
    })
    assert resp.status_code == 201
    data = resp.json()["data"]
    assert data["from_entity_id"] == from_id
    assert data["to_entity_id"] == to_id
    assert data["relation_type"] == "RELATED_TO"
    assert data["description"] == "A와 B의 관계"
    uuid.UUID(data["id"])


async def test_create_relation_unauthenticated_returns_401(client: AsyncClient, admin_client: AsyncClient):
    from_id = await _create_entity(admin_client, "엔티티 A")
    to_id = await _create_entity(admin_client, "엔티티 B")
    resp = await client.post("/relations", json={
        "from_entity_id": from_id,
        "to_entity_id": to_id,
        "relation_type": "RELATED_TO",
    })
    assert resp.status_code == 401


async def test_create_relation_from_entity_not_found(admin_client: AsyncClient):
    to_id = await _create_entity(admin_client)
    resp = await admin_client.post("/relations", json={
        "from_entity_id": str(uuid.uuid4()),
        "to_entity_id": to_id,
        "relation_type": "RELATED_TO",
    })
    assert resp.status_code == 404
    body = resp.json()
    assert body["ok"] is False
    assert body["error"]["code"] == "ENTITY_NOT_FOUND"


async def test_create_relation_to_entity_not_found(admin_client: AsyncClient):
    from_id = await _create_entity(admin_client)
    resp = await admin_client.post("/relations", json={
        "from_entity_id": from_id,
        "to_entity_id": str(uuid.uuid4()),
        "relation_type": "RELATED_TO",
    })
    assert resp.status_code == 404
    body = resp.json()
    assert body["ok"] is False
    assert body["error"]["code"] == "ENTITY_NOT_FOUND"


# ---------------------------------------------------------------------------
# GET /entities/{id}/relations — direction
# ---------------------------------------------------------------------------


async def test_list_relations_direction_out(admin_client: AsyncClient):
    a_id = await _create_entity(admin_client, "A")
    b_id = await _create_entity(admin_client, "B")
    c_id = await _create_entity(admin_client, "C")
    await _create_relation(admin_client, a_id, b_id)   # A→B (outgoing from A)
    await _create_relation(admin_client, c_id, a_id)   # C→A (incoming to A)

    resp = await admin_client.get(f"/entities/{a_id}/relations?direction=out")
    assert resp.status_code == 200
    data = resp.json()["data"]
    assert len(data) == 1
    assert data[0]["from_entity_id"] == a_id
    assert data[0]["to_entity_id"] == b_id


async def test_list_relations_direction_in(admin_client: AsyncClient):
    a_id = await _create_entity(admin_client, "A")
    b_id = await _create_entity(admin_client, "B")
    c_id = await _create_entity(admin_client, "C")
    await _create_relation(admin_client, a_id, b_id)   # A→B
    await _create_relation(admin_client, c_id, a_id)   # C→A (incoming to A)

    resp = await admin_client.get(f"/entities/{a_id}/relations?direction=in")
    assert resp.status_code == 200
    data = resp.json()["data"]
    assert len(data) == 1
    assert data[0]["from_entity_id"] == c_id
    assert data[0]["to_entity_id"] == a_id


async def test_list_relations_direction_both(admin_client: AsyncClient):
    a_id = await _create_entity(admin_client, "A")
    b_id = await _create_entity(admin_client, "B")
    c_id = await _create_entity(admin_client, "C")
    await _create_relation(admin_client, a_id, b_id)
    await _create_relation(admin_client, c_id, a_id)

    resp = await admin_client.get(f"/entities/{a_id}/relations?direction=both")
    assert resp.status_code == 200
    data = resp.json()["data"]
    assert len(data) == 2


async def test_list_relations_invalid_direction(admin_client: AsyncClient):
    a_id = await _create_entity(admin_client, "A")
    resp = await admin_client.get(f"/entities/{a_id}/relations?direction=invalid")
    assert resp.status_code == 400
    body = resp.json()
    assert body["ok"] is False
    assert body["error"]["code"] == "INVALID_DIRECTION"


# ---------------------------------------------------------------------------
# GET /entities/{id}/relations — relation_type filter
# ---------------------------------------------------------------------------


async def test_list_relations_filter_by_type(admin_client: AsyncClient):
    a_id = await _create_entity(admin_client, "A")
    b_id = await _create_entity(admin_client, "B")
    c_id = await _create_entity(admin_client, "C")
    await _create_relation(admin_client, a_id, b_id, "CONTAINS")
    await _create_relation(admin_client, a_id, c_id, "USES")

    resp = await admin_client.get(f"/entities/{a_id}/relations?relation_type=CONTAINS")
    assert resp.status_code == 200
    data = resp.json()["data"]
    assert len(data) == 1
    assert data[0]["relation_type"] == "CONTAINS"


# ---------------------------------------------------------------------------
# GET /entities/{id}/relations — entity not found
# ---------------------------------------------------------------------------


async def test_list_relations_entity_not_found(client: AsyncClient):
    resp = await client.get(f"/entities/{uuid.uuid4()}/relations")
    assert resp.status_code == 404
    body = resp.json()
    assert body["ok"] is False
    assert body["error"]["code"] == "ENTITY_NOT_FOUND"


# ---------------------------------------------------------------------------
# GET /entities/{id}/relations — max_depth BFS
# ---------------------------------------------------------------------------


async def test_list_relations_max_depth_1_only_direct(admin_client: AsyncClient):
    """A→B→C: max_depth=1 from A returns only A→B."""
    a_id = await _create_entity(admin_client, "A")
    b_id = await _create_entity(admin_client, "B")
    c_id = await _create_entity(admin_client, "C")
    await _create_relation(admin_client, a_id, b_id, "CONTAINS")
    await _create_relation(admin_client, b_id, c_id, "CONTAINS")

    resp = await admin_client.get(f"/entities/{a_id}/relations?direction=out&max_depth=1")
    assert resp.status_code == 200
    data = resp.json()["data"]
    assert len(data) == 1
    assert data[0]["from_entity_id"] == a_id
    assert data[0]["to_entity_id"] == b_id


async def test_list_relations_max_depth_2_includes_chain(admin_client: AsyncClient):
    """A→B→C: max_depth=2 from A returns both A→B and B→C."""
    a_id = await _create_entity(admin_client, "A")
    b_id = await _create_entity(admin_client, "B")
    c_id = await _create_entity(admin_client, "C")
    await _create_relation(admin_client, a_id, b_id, "CONTAINS")
    await _create_relation(admin_client, b_id, c_id, "CONTAINS")

    resp = await admin_client.get(f"/entities/{a_id}/relations?direction=out&max_depth=2")
    assert resp.status_code == 200
    data = resp.json()["data"]
    assert len(data) == 2
    from_ids = {r["from_entity_id"] for r in data}
    assert a_id in from_ids
    assert b_id in from_ids


async def test_list_relations_empty(admin_client: AsyncClient):
    a_id = await _create_entity(admin_client, "A")
    resp = await admin_client.get(f"/entities/{a_id}/relations")
    assert resp.status_code == 200
    assert resp.json()["data"] == []
