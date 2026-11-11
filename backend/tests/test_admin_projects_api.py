"""Tests for /admin/projects endpoints."""
from httpx import AsyncClient

from tests.conftest import bearer
from app.db.session import async_session_factory
from app.service.project_service import ProjectService


async def create_project(project_id: str, alias: str) -> None:
    async with async_session_factory() as session:
        await ProjectService(session).create_project(id=project_id, alias=alias, description=None)


# ---------------------------------------------------------------------------
# GET /admin/projects
# ---------------------------------------------------------------------------


async def test_list_admin_projects(admin_client: AsyncClient):
    await create_project("proja", "Project 1")
    await create_project("projb", "Project 2")

    resp = await admin_client.get("/admin/projects")
    assert resp.status_code == 200
    data = resp.json()["data"]
    assert len(data) >= 2


async def test_list_admin_projects_filter_active(admin_client: AsyncClient):
    await create_project("activeone", "Active")
    await create_project("inactone", "Inactive")

    await admin_client.patch("/admin/projects/inactone", json={"is_active": False})

    resp = await admin_client.get("/admin/projects?is_active=true")
    assert resp.status_code == 200
    data = resp.json()["data"]
    assert all(p["is_active"] for p in data)


async def test_list_admin_projects_search(admin_client: AsyncClient):
    await create_project("searchone", "Unicorn Project")
    await create_project("otherone", "Other Project")

    resp = await admin_client.get("/admin/projects?search=Unicorn")
    assert resp.status_code == 200
    data = resp.json()["data"]
    assert all("Unicorn" in p["alias"] or "unicorn" in p["id"] for p in data)


async def test_list_projects_forbidden_non_admin(client: AsyncClient, write_key: str):
    resp = await client.get("/admin/projects", headers=bearer(write_key))
    assert resp.status_code == 403


# ---------------------------------------------------------------------------
# POST /admin/projects
# ---------------------------------------------------------------------------


async def test_create_project(admin_client: AsyncClient):
    resp = await admin_client.post("/admin/projects", json={"id": "testproj", "alias": "Test Project"})
    assert resp.status_code == 201
    data = resp.json()["data"]
    assert data["id"] == "testproj"
    assert data["alias"] == "Test Project"
    assert data["is_active"] is True


async def test_create_project_duplicate(admin_client: AsyncClient):
    await admin_client.post("/admin/projects", json={"id": "dup", "alias": "Dup"})
    resp = await admin_client.post("/admin/projects", json={"id": "dup", "alias": "Dup2"})
    assert resp.status_code == 409


async def test_create_project_invalid_id(admin_client: AsyncClient):
    # too short
    resp = await admin_client.post("/admin/projects", json={"id": "AB", "alias": "X"})
    assert resp.status_code == 422

    # disallowed character (space)
    resp2 = await admin_client.post("/admin/projects", json={"id": "no space", "alias": "X"})
    assert resp2.status_code == 422

    # disallowed character (!)
    resp3 = await admin_client.post("/admin/projects", json={"id": "bad!id", "alias": "X"})
    assert resp3.status_code == 422


# ---------------------------------------------------------------------------
# PATCH /admin/projects/{project_id}
# ---------------------------------------------------------------------------


async def test_update_project_alias(admin_client: AsyncClient):
    await create_project("updone", "Old Name")

    resp = await admin_client.patch("/admin/projects/updone", json={"alias": "New Name"})
    assert resp.status_code == 200
    assert resp.json()["data"]["alias"] == "New Name"


async def test_update_project_deactivate(admin_client: AsyncClient):
    await create_project("deactone", "Deactivate Me")

    resp = await admin_client.patch("/admin/projects/deactone", json={"is_active": False})
    assert resp.status_code == 200
    assert resp.json()["data"]["is_active"] is False


async def test_update_project_not_found(admin_client: AsyncClient):
    resp = await admin_client.patch("/admin/projects/nonexistent", json={"alias": "X"})
    assert resp.status_code == 404
