"""Entity list API tests — GET /entities."""

import uuid
from httpx import AsyncClient
from app.db.session import async_session_factory
from app.service.auth_service import AuthService
from app.service.project_service import ProjectService


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


# ---------------------------------------------------------------------------
# Project ID filter tests
# ---------------------------------------------------------------------------

async def _create_project(alias: str) -> str:
    project_id = alias.upper()
    async with async_session_factory() as session:
        admin = await AuthService(session).create_user(
            login_id=f"admin_{alias.lower()}",
            password="pass123",
            display_name=alias,
            role="admin",
        )
        await ProjectService(session).create_project(
            id=project_id, alias=alias, description=None, created_by=admin.id
        )
    return project_id


async def test_list_entities_filter_project_id(admin_client: AsyncClient):
    """GET /entities?project_id=X returns only entities in that project."""
    proj_a = await _create_project("PROJ_A")
    proj_b = await _create_project("PROJ_B")

    id_a = await _create(admin_client, type="FEATURE", canonical_name="feat-a", project_id=proj_a)
    await _create(admin_client, type="FEATURE", canonical_name="feat-b", project_id=proj_b)

    resp = await admin_client.get("/entities", params={"project_id": proj_a})
    assert resp.status_code == 200
    data = resp.json()["data"]
    assert data["total"] == 1
    assert data["items"][0]["id"] == id_a


async def test_list_entities_filter_project_id_inaccessible_returns_empty(client: AsyncClient, admin_client: AsyncClient):
    """Unauthenticated user gets empty list when filtering by a project_id they cannot see."""
    proj = await _create_project("PRIVATE_PROJ")
    await _create(admin_client, type="FEATURE", canonical_name="secret-feat", project_id=proj)

    resp = await client.get("/entities", params={"project_id": proj})
    assert resp.status_code == 200
    data = resp.json()["data"]
    assert data["total"] == 0
    assert data["items"] == []
