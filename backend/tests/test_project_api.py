"""Tests for project & membership API (Step 2-2)."""
from __future__ import annotations

import uuid
import pytest
from httpx import AsyncClient

from app.db.session import async_session_factory
from app.service.auth_service import AuthService


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

async def _create_user(email: str, password: str = "pw123", role: str = "user") -> dict:
    async with async_session_factory() as session:
        user = await AuthService(session).create_user(
            email=email, password=password, display_name="Test User", role=role
        )
    return {"id": str(user.id), "email": email, "password": password}


async def _login(client: AsyncClient, email: str, password: str) -> None:
    resp = await client.post("/auth/login", json={"email": email, "password": password})
    assert resp.status_code == 200, resp.text


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
async def test_create_project_non_admin_returns_403(client: AsyncClient):
    user = await _create_user("user@test.com")
    await _login(client, user["email"], user["password"])
    resp = await client.post("/projects", json={"id": "Beta", "alias": "베타"})
    assert resp.status_code == 403


@pytest.mark.asyncio
async def test_create_project_unauthenticated_returns_401(client: AsyncClient):
    resp = await client.post("/projects", json={"id": "Beta", "alias": "베타"})
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_create_project_invalid_id_returns_422(admin_client: AsyncClient):
    # ID too short
    resp = await admin_client.post("/projects", json={"id": "AB", "alias": "alias"})
    assert resp.status_code == 422

    # ID with numbers
    resp2 = await admin_client.post("/projects", json={"id": "Alpha123", "alias": "alias"})
    assert resp2.status_code == 422

    # ID too long
    resp3 = await admin_client.post("/projects", json={"id": "A" * 21, "alias": "alias"})
    assert resp3.status_code == 422


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
# Step 2-2-2: Membership
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_admin_can_add_member(admin_client: AsyncClient):
    user = await _create_user("member@test.com")
    await admin_client.post("/projects", json={"id": "Eps", "alias": "엡실론"})

    resp = await admin_client.post("/projects/Eps/members", json={
        "user_id": user["id"],
        "role": "member",
    })
    assert resp.status_code == 201
    data = resp.json()["data"]
    assert data["project_id"] == "Eps"
    assert data["user_id"] == user["id"]
    assert data["role"] == "member"


@pytest.mark.asyncio
async def test_admin_can_assign_project_admin_role(admin_client: AsyncClient):
    user = await _create_user("pa@test.com")
    await admin_client.post("/projects", json={"id": "Zeta", "alias": "제타"})
    resp = await admin_client.post("/projects/Zeta/members", json={
        "user_id": user["id"],
        "role": "project_admin",
    })
    assert resp.status_code == 201
    assert resp.json()["data"]["role"] == "project_admin"


@pytest.mark.asyncio
async def test_non_admin_non_project_admin_cannot_add_member(client: AsyncClient, admin_client: AsyncClient):
    """Regular member cannot manage membership."""
    member = await _create_user("member2@test.com")
    other = await _create_user("other@test.com")
    await admin_client.post("/projects", json={"id": "Eta", "alias": "에타"})
    await admin_client.post("/projects/Eta/members", json={"user_id": member["id"], "role": "member"})

    await _login(client, member["email"], member["password"])
    resp = await client.post("/projects/Eta/members", json={"user_id": other["id"], "role": "member"})
    assert resp.status_code == 403


@pytest.mark.asyncio
async def test_project_admin_can_add_member(client: AsyncClient, admin_client: AsyncClient):
    """project_admin can add members but not project_admin role."""
    pa = await _create_user("pa2@test.com")
    member = await _create_user("newmember@test.com")
    await admin_client.post("/projects", json={"id": "Theta", "alias": "세타"})
    await admin_client.post("/projects/Theta/members", json={"user_id": pa["id"], "role": "project_admin"})

    await _login(client, pa["email"], pa["password"])
    resp = await client.post("/projects/Theta/members", json={"user_id": member["id"], "role": "member"})
    assert resp.status_code == 201


@pytest.mark.asyncio
async def test_project_admin_cannot_assign_project_admin_role(client: AsyncClient, admin_client: AsyncClient):
    pa = await _create_user("pa3@test.com")
    other = await _create_user("other2@test.com")
    await admin_client.post("/projects", json={"id": "Iota", "alias": "이오타"})
    await admin_client.post("/projects/Iota/members", json={"user_id": pa["id"], "role": "project_admin"})

    await _login(client, pa["email"], pa["password"])
    resp = await client.post("/projects/Iota/members", json={"user_id": other["id"], "role": "project_admin"})
    assert resp.status_code == 403


@pytest.mark.asyncio
async def test_list_members(admin_client: AsyncClient):
    user1 = await _create_user("m1@test.com")
    user2 = await _create_user("m2@test.com")
    await admin_client.post("/projects", json={"id": "Kappa", "alias": "카파"})
    await admin_client.post("/projects/Kappa/members", json={"user_id": user1["id"], "role": "member"})
    await admin_client.post("/projects/Kappa/members", json={"user_id": user2["id"], "role": "member"})

    resp = await admin_client.get("/projects/Kappa/members")
    assert resp.status_code == 200
    member_ids = [m["user_id"] for m in resp.json()["data"]]
    assert user1["id"] in member_ids
    assert user2["id"] in member_ids


@pytest.mark.asyncio
async def test_remove_member(admin_client: AsyncClient):
    user = await _create_user("rm@test.com")
    await admin_client.post("/projects", json={"id": "Lambda", "alias": "람다"})
    await admin_client.post("/projects/Lambda/members", json={"user_id": user["id"], "role": "member"})

    resp = await admin_client.delete(f"/projects/Lambda/members/{user['id']}")
    assert resp.status_code == 200

    list_resp = await admin_client.get("/projects/Lambda/members")
    member_ids = [m["user_id"] for m in list_resp.json()["data"]]
    assert user["id"] not in member_ids


@pytest.mark.asyncio
async def test_update_member_role(admin_client: AsyncClient):
    user = await _create_user("role@test.com")
    await admin_client.post("/projects", json={"id": "Muuuu", "alias": "뮤"})
    await admin_client.post("/projects/Muuuu/members", json={"user_id": user["id"], "role": "member"})

    resp = await admin_client.put(f"/projects/Muuuu/members/{user['id']}/role", json={"role": "project_admin"})
    assert resp.status_code == 200
    assert resp.json()["data"]["role"] == "project_admin"


# ---------------------------------------------------------------------------
# Step 2-2-3 & 2-2-4: Entity project_id + access policy
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_create_project_entity_as_member(client: AsyncClient, admin_client: AsyncClient):
    """Project members can create entities in their project."""
    user = await _create_user("projuser@test.com")
    await admin_client.post("/projects", json={"id": "Nuuuu", "alias": "뉴"})
    await admin_client.post("/projects/Nuuuu/members", json={"user_id": user["id"], "role": "member"})

    await _login(client, user["email"], user["password"])
    resp = await client.post("/entities", json={
        "type": "FEATURE",
        "canonical_name": "프로젝트 기능",
        "project_id": "Nuuuu",
    })
    assert resp.status_code == 201


@pytest.mark.asyncio
async def test_create_public_entity_as_non_admin_forbidden(client: AsyncClient):
    """Non-admin cannot create public (project_id=None) entities."""
    user = await _create_user("nonadmin@test.com")
    await _login(client, user["email"], user["password"])

    resp = await client.post("/entities", json={
        "type": "FEATURE",
        "canonical_name": "공개 기능",
    })
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

    # Unauthenticated cannot see project entity
    get_resp = await client.get(f"/entities/{entity_id}")
    assert get_resp.status_code == 401

    # Unauthenticated list shows no project entities
    list_resp = await client.get("/entities")
    ids = [e["id"] for e in list_resp.json()["data"]["items"]]
    assert entity_id not in ids


@pytest.mark.asyncio
async def test_project_entity_visible_to_member(client: AsyncClient, admin_client: AsyncClient):
    """Project members can see their project's entities."""
    user = await _create_user("viewer@test.com")
    await admin_client.post("/projects", json={"id": "Omicron", "alias": "오미크론"})
    await admin_client.post("/projects/Omicron/members", json={"user_id": user["id"], "role": "member"})

    entity_resp = await admin_client.post("/entities", json={
        "type": "FEATURE",
        "canonical_name": "팀원 공개 기능",
        "project_id": "Omicron",
    })
    entity_id = entity_resp.json()["data"]["id"]

    await _login(client, user["email"], user["password"])
    get_resp = await client.get(f"/entities/{entity_id}")
    assert get_resp.status_code == 200
    assert get_resp.json()["data"]["project_id"] == "Omicron"


@pytest.mark.asyncio
async def test_project_entity_hidden_from_non_member(client: AsyncClient, admin_client: AsyncClient):
    """Non-members cannot see project entities."""
    user = await _create_user("outsider@test.com")
    await admin_client.post("/projects", json={"id": "Pii", "alias": "파이"})

    entity_resp = await admin_client.post("/entities", json={
        "type": "FEATURE",
        "canonical_name": "파이 기능",
        "project_id": "Pii",
    })
    entity_id = entity_resp.json()["data"]["id"]

    await _login(client, user["email"], user["password"])
    get_resp = await client.get(f"/entities/{entity_id}")
    assert get_resp.status_code == 403


@pytest.mark.asyncio
async def test_member_can_modify_project_entity(client: AsyncClient, admin_client: AsyncClient):
    """Project members can modify their project's entities."""
    user = await _create_user("editor@test.com")
    await admin_client.post("/projects", json={"id": "Rho", "alias": "로"})
    await admin_client.post("/projects/Rho/members", json={"user_id": user["id"], "role": "member"})

    entity_resp = await admin_client.post("/entities", json={
        "type": "FEATURE",
        "canonical_name": "수정 대상 기능",
        "project_id": "Rho",
    })
    entity_id = entity_resp.json()["data"]["id"]

    await _login(client, user["email"], user["password"])
    patch_resp = await client.patch(f"/entities/{entity_id}", json={"canonical_name": "수정됨"})
    assert patch_resp.status_code == 200
    assert patch_resp.json()["data"]["canonical_name"] == "수정됨"


@pytest.mark.asyncio
async def test_public_entity_and_project_entity_in_list(client: AsyncClient, admin_client: AsyncClient):
    """Authenticated user sees public + their project entities."""
    user = await _create_user("listuser@test.com")
    await admin_client.post("/projects", json={"id": "Sigma", "alias": "시그마"})
    await admin_client.post("/projects/Sigma/members", json={"user_id": user["id"], "role": "member"})

    # public entity
    pub_resp = await admin_client.post("/entities", json={
        "type": "FEATURE", "canonical_name": "공개 기능 Sigma",
    })
    pub_id = pub_resp.json()["data"]["id"]

    # project entity
    proj_resp = await admin_client.post("/entities", json={
        "type": "FEATURE", "canonical_name": "프로젝트 기능 Sigma", "project_id": "Sigma",
    })
    proj_id = proj_resp.json()["data"]["id"]

    # another project entity (user is NOT a member)
    await admin_client.post("/projects", json={"id": "Tau", "alias": "타우"})
    other_resp = await admin_client.post("/entities", json={
        "type": "FEATURE", "canonical_name": "타우 기능", "project_id": "Tau",
    })
    other_id = other_resp.json()["data"]["id"]

    await _login(client, user["email"], user["password"])
    list_resp = await client.get("/entities")
    ids = [e["id"] for e in list_resp.json()["data"]["items"]]

    assert pub_id in ids          # public: visible
    assert proj_id in ids         # own project: visible
    assert other_id not in ids    # other project: hidden
