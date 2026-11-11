"""Tests for project API and key-scoped entity access."""
from __future__ import annotations

import pytest
from httpx import AsyncClient

from tests.conftest import bearer, create_key

# ---------------------------------------------------------------------------
# Step 2-2-1: Project CRUD
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_create_project_as_admin(admin_client: AsyncClient):
    resp = await admin_client.post("/projects", json={
        "id": "Alpha",
        "alias": "알파 프로젝트",
        "description": "첫 번째 프로젝트",
    })
    assert resp.status_code == 201
    data = resp.json()["data"]
    assert data["id"] == "Alpha"
    assert data["alias"] == "알파 프로젝트"
    assert data["is_active"] is True


@pytest.mark.asyncio
async def test_create_project_non_admin_returns_403(client: AsyncClient, write_key: str):
    resp = await client.post("/projects", json={"id": "Beta", "alias": "베타"}, headers=bearer(write_key))
    assert resp.status_code == 403


@pytest.mark.asyncio
async def test_create_project_unauthenticated_returns_401(client: AsyncClient):
    resp = await client.post("/projects", json={"id": "Beta", "alias": "베타"})
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_create_project_invalid_id_returns_422(admin_client: AsyncClient):
    # ID too short (2 chars)
    resp = await admin_client.post("/projects", json={"id": "AB", "alias": "alias"})
    assert resp.status_code == 422

    # ID too long (51 chars)
    resp2 = await admin_client.post("/projects", json={"id": "A" * 51, "alias": "alias"})
    assert resp2.status_code == 422

    # ID with disallowed characters (space, !, %, hyphen, hash, at, caret)
    resp3 = await admin_client.post("/projects", json={"id": "no space", "alias": "alias"})
    assert resp3.status_code == 422

    resp4 = await admin_client.post("/projects", json={"id": "has!bang", "alias": "alias"})
    assert resp4.status_code == 422

    resp5 = await admin_client.post("/projects", json={"id": "pct%25", "alias": "alias"})
    assert resp5.status_code == 422

    resp6 = await admin_client.post("/projects", json={"id": "my-project", "alias": "alias"})
    assert resp6.status_code == 422

    resp7 = await admin_client.post("/projects", json={"id": "team#sub", "alias": "alias"})
    assert resp7.status_code == 422

    resp8 = await admin_client.post("/projects", json={"id": "v2@corp", "alias": "alias"})
    assert resp8.status_code == 422

    resp9 = await admin_client.post("/projects", json={"id": "a^b_c", "alias": "alias"})
    assert resp9.status_code == 422


@pytest.mark.asyncio
@pytest.mark.parametrize("project_id", [
    "ABC123",
    "my_project",
    "v2_api",
    "team_sub_v2",
    "UPPER_lower_123",
])
async def test_create_project_valid_underscore_ids(admin_client: AsyncClient, project_id: str):
    resp = await admin_client.post("/projects", json={"id": project_id, "alias": "alias"})
    assert resp.status_code == 201, f"Expected 201 for id={project_id!r}, got {resp.status_code}: {resp.text}"


@pytest.mark.asyncio
async def test_create_project_duplicate_id_returns_409(admin_client: AsyncClient):
    await admin_client.post("/projects", json={"id": "Gamma", "alias": "감마"})
    resp = await admin_client.post("/projects", json={"id": "Gamma", "alias": "감마2"})
    assert resp.status_code == 409


@pytest.mark.asyncio
async def test_get_project(admin_client: AsyncClient):
    await admin_client.post("/projects", json={"id": "Delta", "alias": "델타"})
    resp = await admin_client.get("/projects/Delta")
    assert resp.status_code == 200
    assert resp.json()["data"]["id"] == "Delta"


@pytest.mark.asyncio
async def test_get_project_not_found(admin_client: AsyncClient):
    resp = await admin_client.get("/projects/NotExist")
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_list_projects(admin_client: AsyncClient):
    await admin_client.post("/projects", json={"id": "ProjOne", "alias": "프로젝트1"})
    await admin_client.post("/projects", json={"id": "ProjTwo", "alias": "프로젝트2"})
    resp = await admin_client.get("/projects")
    assert resp.status_code == 200
    ids = [p["id"] for p in resp.json()["data"]]
    assert "ProjOne" in ids
    assert "ProjTwo" in ids


# ---------------------------------------------------------------------------
# Entity project_id + access policy (project API keys)
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_list_and_get_projects_scoped_to_key(admin_client: AsyncClient, client: AsyncClient):
    await admin_client.post("/projects", json={"id": "Mine", "alias": "내 것"})
    await admin_client.post("/projects", json={"id": "Other", "alias": "남의 것"})
    key = await create_key("Mine", "read")

    resp = await client.get("/projects", headers=bearer(key))
    assert [p["id"] for p in resp.json()["data"]] == ["Mine"]
    assert (await client.get("/projects/Mine", headers=bearer(key))).status_code == 200
    assert (await client.get("/projects/Other", headers=bearer(key))).status_code == 403


@pytest.mark.asyncio
async def test_create_project_entity_with_write_key(client: AsyncClient, admin_client: AsyncClient):
    await admin_client.post("/projects", json={"id": "Nuuuu", "alias": "뉴"})
    key = await create_key("Nuuuu", "write")
    resp = await client.post("/entities", json={
        "type": "FEATURE",
        "canonical_name": "프로젝트 기능",
        "project_id": "Nuuuu",
    }, headers=bearer(key))
    assert resp.status_code == 201


@pytest.mark.asyncio
async def test_create_public_entity_with_key_forbidden(client: AsyncClient, write_key: str):
    resp = await client.post("/entities", json={
        "type": "FEATURE",
        "canonical_name": "공개 기능",
    }, headers=bearer(write_key))
    assert resp.status_code == 403


@pytest.mark.asyncio
async def test_project_entity_hidden_from_unauthenticated(admin_client: AsyncClient, client: AsyncClient):
    """Project entities are not visible to unauthenticated users."""
    await admin_client.post("/projects", json={"id": "Xii", "alias": "크사이"})
    resp = await admin_client.post("/entities", json={
        "type": "FEATURE",
        "canonical_name": "숨겨진 기능",
        "project_id": "Xii",
    })
    entity_id = resp.json()["data"]["id"]

    get_resp = await client.get(f"/entities/{entity_id}")
    assert get_resp.status_code == 401

    list_resp = await client.get("/entities")
    ids = [e["id"] for e in list_resp.json()["data"]["items"]]
    assert entity_id not in ids


@pytest.mark.asyncio
async def test_write_key_can_modify_own_project_entity(client: AsyncClient, admin_client: AsyncClient):
    await admin_client.post("/projects", json={"id": "Rho", "alias": "로"})
    entity_resp = await admin_client.post("/entities", json={
        "type": "FEATURE",
        "canonical_name": "수정 대상 기능",
        "project_id": "Rho",
    })
    entity_id = entity_resp.json()["data"]["id"]

    key = await create_key("Rho", "write")
    patch_resp = await client.patch(
        f"/entities/{entity_id}", json={"canonical_name": "수정됨"}, headers=bearer(key)
    )
    assert patch_resp.status_code == 200
    assert patch_resp.json()["data"]["canonical_name"] == "수정됨"


@pytest.mark.asyncio
async def test_public_entity_and_project_entity_in_list(client: AsyncClient, admin_client: AsyncClient):
    """A key sees public + its own project entities, never another project's."""
    await admin_client.post("/projects", json={"id": "Sigma", "alias": "시그마"})
    await admin_client.post("/projects", json={"id": "Tau", "alias": "타우"})
    pub_id = (await admin_client.post("/entities", json={
        "type": "FEATURE", "canonical_name": "공개 기능 Sigma",
    })).json()["data"]["id"]
    proj_id = (await admin_client.post("/entities", json={
        "type": "FEATURE", "canonical_name": "프로젝트 기능 Sigma", "project_id": "Sigma",
    })).json()["data"]["id"]
    other_id = (await admin_client.post("/entities", json={
        "type": "FEATURE", "canonical_name": "타우 기능", "project_id": "Tau",
    })).json()["data"]["id"]

    key = await create_key("Sigma", "read")
    list_resp = await client.get("/entities", headers=bearer(key))
    ids = [e["id"] for e in list_resp.json()["data"]["items"]]

    assert pub_id in ids
    assert proj_id in ids
    assert other_id not in ids
