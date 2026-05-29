"""Entity list API tests — GET /entities."""

from httpx import AsyncClient


async def _create(admin_client: AsyncClient, **kwargs) -> str:
    resp = await admin_client.post("/entities", json=kwargs)
    assert resp.status_code == 201
    return resp.json()["data"]["id"]


async def test_list_entities_empty(client: AsyncClient):
    resp = await client.get("/entities")
    assert resp.status_code == 200
    body = resp.json()
    assert body["ok"] is True
    assert body["data"]["items"] == []
    assert body["data"]["total"] == 0


async def test_list_entities_basic(admin_client: AsyncClient):
    for i in range(3):
        await _create(admin_client, type="FEATURE", canonical_name=f"feature-{i}")

    resp = await admin_client.get("/entities")
    assert resp.status_code == 200
    data = resp.json()["data"]
    assert data["total"] == 3
    assert len(data["items"]) == 3


async def test_list_entities_filter_status(admin_client: AsyncClient):
    id1 = await _create(admin_client, type="FEATURE", canonical_name="cand-1", status="candidate")
    id2 = await _create(admin_client, type="FEATURE", canonical_name="cand-2", status="candidate")
    await _create(admin_client, type="FEATURE", canonical_name="active-1", status="active")

    resp = await admin_client.get("/entities", params={"status": "candidate"})
    assert resp.status_code == 200
    data = resp.json()["data"]
    assert data["total"] == 2
    ids = {item["id"] for item in data["items"]}
    assert id1 in ids and id2 in ids


async def test_list_entities_filter_types(admin_client: AsyncClient):
    id1 = await _create(admin_client, type="UI_AREA", canonical_name="ui-1")
    id2 = await _create(admin_client, type="UI_AREA", canonical_name="ui-2")
    await _create(admin_client, type="FEATURE", canonical_name="feat-1")

    resp = await admin_client.get("/entities", params={"types": "UI_AREA"})
    assert resp.status_code == 200
    data = resp.json()["data"]
    assert data["total"] == 2
    ids = {item["id"] for item in data["items"]}
    assert id1 in ids and id2 in ids


async def test_list_entities_pagination(admin_client: AsyncClient):
    for i in range(5):
        await _create(admin_client, type="FEATURE", canonical_name=f"page-{i}")

    resp1 = await admin_client.get("/entities", params={"limit": 2, "offset": 0})
    assert resp1.status_code == 200
    data1 = resp1.json()["data"]
    assert data1["total"] == 5
    assert len(data1["items"]) == 2

    resp2 = await admin_client.get("/entities", params={"limit": 2, "offset": 4})
    assert resp2.status_code == 200
    data2 = resp2.json()["data"]
    assert data2["total"] == 5
    assert len(data2["items"]) == 1


async def test_list_entities_sort_canonical_name(admin_client: AsyncClient):
    for name in ["charlie", "alpha", "bravo"]:
        await _create(admin_client, type="FEATURE", canonical_name=name)

    resp = await admin_client.get("/entities", params={"sort": "canonical_name", "order": "asc"})
    assert resp.status_code == 200
    names = [item["canonical_name"] for item in resp.json()["data"]["items"]]
    assert names == sorted(names)


async def test_list_entities_invalid_sort(client: AsyncClient):
    resp = await client.get("/entities", params={"sort": "invalid"})
    assert resp.status_code == 422


async def test_list_entities_limit_max(client: AsyncClient):
    resp = await client.get("/entities", params={"limit": 101})
    assert resp.status_code == 422
