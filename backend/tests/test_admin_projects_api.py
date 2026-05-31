"""Tests for /admin/projects endpoints."""
import uuid
import pytest
from httpx import AsyncClient

from app.db.session import async_session_factory
from app.service.auth_service import AuthService
from app.service.project_service import ProjectService


async def _create_user(login_id: str, role: str = "user") -> str:
    async with async_session_factory() as session:
        user = await AuthService(session).create_user(
            login_id=login_id, password="pass123", display_name=login_id, role=role
        )
    return str(user.id)


async def _create_project(project_id: str, alias: str, admin_id: str) -> None:
    async with async_session_factory() as session:
        await ProjectService(session).create_project(
            id=project_id, alias=alias, description=None, created_by=uuid.UUID(admin_id)
        )


# ---------------------------------------------------------------------------
# GET /admin/projects
# ---------------------------------------------------------------------------


async def test_list_admin_projects(admin_client: AsyncClient):
    admin_resp = await admin_client.get("/auth/me")
    admin_id = admin_resp.json()["data"]["id"]
    await _create_project("proja", "Project 1", admin_id)
    await _create_project("projb", "Project 2", admin_id)

    resp = await admin_client.get("/admin/projects")
    assert resp.status_code == 200
    data = resp.json()["data"]
    assert len(data) >= 2


async def test_list_admin_projects_filter_active(admin_client: AsyncClient):
    admin_resp = await admin_client.get("/auth/me")
    admin_id = admin_resp.json()["data"]["id"]
    await _create_project("activeone", "Active", admin_id)
    await _create_project("inactone", "Inactive", admin_id)

    await admin_client.patch("/admin/projects/inactone", json={"is_active": False})

    resp = await admin_client.get("/admin/projects?is_active=true")
    assert resp.status_code == 200
    data = resp.json()["data"]
    assert all(p["is_active"] for p in data)


async def test_list_admin_projects_search(admin_client: AsyncClient):
    admin_resp = await admin_client.get("/auth/me")
    admin_id = admin_resp.json()["data"]["id"]
    await _create_project("searchone", "Unicorn Project", admin_id)
    await _create_project("otherone", "Other Project", admin_id)

    resp = await admin_client.get("/admin/projects?search=Unicorn")
    assert resp.status_code == 200
    data = resp.json()["data"]
    assert all("Unicorn" in p["alias"] or "unicorn" in p["id"] for p in data)


async def test_list_projects_forbidden_non_admin(client: AsyncClient):
    uid = await _create_user("user_test")
    await client.post("/auth/login", json={"login_id": "user_test", "password": "pass123"})
    resp = await client.get("/admin/projects")
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
    admin_resp = await admin_client.get("/auth/me")
    admin_id = admin_resp.json()["data"]["id"]
    await _create_project("updone", "Old Name", admin_id)

    resp = await admin_client.patch("/admin/projects/updone", json={"alias": "New Name"})
    assert resp.status_code == 200
    assert resp.json()["data"]["alias"] == "New Name"


async def test_update_project_deactivate(admin_client: AsyncClient):
    admin_resp = await admin_client.get("/auth/me")
    admin_id = admin_resp.json()["data"]["id"]
    await _create_project("deactone", "Deactivate Me", admin_id)

    resp = await admin_client.patch("/admin/projects/deactone", json={"is_active": False})
    assert resp.status_code == 200
    assert resp.json()["data"]["is_active"] is False


async def test_update_project_not_found(admin_client: AsyncClient):
    resp = await admin_client.patch("/admin/projects/nonexistent", json={"alias": "X"})
    assert resp.status_code == 404


# ---------------------------------------------------------------------------
# GET /admin/projects/{project_id}/members
# ---------------------------------------------------------------------------


async def test_get_members_admin_only(admin_client: AsyncClient, client: AsyncClient):
    admin_resp = await admin_client.get("/auth/me")
    admin_id = admin_resp.json()["data"]["id"]
    await _create_project("mbrproj", "Member Project", admin_id)

    uid = await _create_user("member_test")
    await admin_client.post("/admin/projects/mbrproj/members", json={"user_id": uid, "role": "member"})

    resp = await admin_client.get("/admin/projects/mbrproj/members")
    assert resp.status_code == 200
    data = resp.json()["data"]
    assert any(m["user_id"] == uid for m in data)


# ---------------------------------------------------------------------------
# POST /admin/projects/{project_id}/members
# ---------------------------------------------------------------------------


async def test_add_member(admin_client: AsyncClient):
    admin_resp = await admin_client.get("/auth/me")
    admin_id = admin_resp.json()["data"]["id"]
    await _create_project("addmbrp", "Add Member Project", admin_id)
    uid = await _create_user("newmember_test")

    resp = await admin_client.post("/admin/projects/addmbrp/members", json={"user_id": uid, "role": "member"})
    assert resp.status_code == 201
    data = resp.json()["data"]
    assert data["user_id"] == uid
    assert data["role"] == "member"


async def test_add_project_admin_member(admin_client: AsyncClient):
    admin_resp = await admin_client.get("/auth/me")
    admin_id = admin_resp.json()["data"]["id"]
    await _create_project("padminp", "Project Admin Project", admin_id)
    uid = await _create_user("padmin_test")

    resp = await admin_client.post("/admin/projects/padminp/members", json={"user_id": uid, "role": "project_admin"})
    assert resp.status_code == 201
    assert resp.json()["data"]["role"] == "project_admin"


# ---------------------------------------------------------------------------
# PATCH /admin/projects/{project_id}/members/{user_id}
# ---------------------------------------------------------------------------


async def test_update_member_role(admin_client: AsyncClient):
    admin_resp = await admin_client.get("/auth/me")
    admin_id = admin_resp.json()["data"]["id"]
    await _create_project("roleproj", "Role Project", admin_id)
    uid = await _create_user("role_test")
    await admin_client.post("/admin/projects/roleproj/members", json={"user_id": uid, "role": "member"})

    resp = await admin_client.patch(f"/admin/projects/roleproj/members/{uid}", json={"role": "project_admin"})
    assert resp.status_code == 200
    assert resp.json()["data"]["role"] == "project_admin"


# ---------------------------------------------------------------------------
# DELETE /admin/projects/{project_id}/members/{user_id}
# ---------------------------------------------------------------------------


async def test_remove_member(admin_client: AsyncClient):
    admin_resp = await admin_client.get("/auth/me")
    admin_id = admin_resp.json()["data"]["id"]
    await _create_project("rmproj", "Remove Project", admin_id)
    uid = await _create_user("rm_test")
    await admin_client.post("/admin/projects/rmproj/members", json={"user_id": uid, "role": "member"})

    resp = await admin_client.delete(f"/admin/projects/rmproj/members/{uid}")
    assert resp.status_code == 200

    members_resp = await admin_client.get("/admin/projects/rmproj/members")
    members = members_resp.json()["data"]
    assert all(m["user_id"] != uid or not m["is_active"] for m in members)


async def test_remove_nonexistent_member(admin_client: AsyncClient):
    admin_resp = await admin_client.get("/auth/me")
    admin_id = admin_resp.json()["data"]["id"]
    await _create_project("rmprojb", "Remove Project 2", admin_id)

    resp = await admin_client.delete(f"/admin/projects/rmprojb/members/{uuid.uuid4()}")
    assert resp.status_code == 404


# ---------------------------------------------------------------------------
# project_admin role — GET /admin/projects
# ---------------------------------------------------------------------------


async def test_project_admin_no_membership_returns_empty(project_admin_client: AsyncClient):
    """project_admin with no membership gets empty list, not 403."""
    resp = await project_admin_client.get("/admin/projects")
    assert resp.status_code == 200
    assert resp.json()["data"] == []


async def test_project_admin_can_list_own_projects(
    admin_client: AsyncClient,
    project_admin_client: AsyncClient,
):
    """project_admin sees only projects they are a member of."""
    admin_resp = await admin_client.get("/auth/me")
    admin_id = admin_resp.json()["data"]["id"]
    await _create_project("pa_own", "Own Project", admin_id)
    await _create_project("pa_other", "Other Project", admin_id)

    padmin_resp = await project_admin_client.get("/auth/me")
    padmin_id = padmin_resp.json()["data"]["id"]
    await admin_client.post("/admin/projects/pa_own/members", json={"user_id": padmin_id, "role": "member"})

    resp = await project_admin_client.get("/admin/projects")
    assert resp.status_code == 200
    ids = [p["id"] for p in resp.json()["data"]]
    assert "pa_own" in ids
    assert "pa_other" not in ids


async def test_project_admin_cannot_list_other_projects(
    admin_client: AsyncClient,
    project_admin_client: AsyncClient,
):
    """project_admin without membership cannot see other projects."""
    admin_resp = await admin_client.get("/auth/me")
    admin_id = admin_resp.json()["data"]["id"]
    await _create_project("pa_secret", "Secret Project", admin_id)

    resp = await project_admin_client.get("/admin/projects")
    assert resp.status_code == 200
    ids = [p["id"] for p in resp.json()["data"]]
    assert "pa_secret" not in ids


async def test_user_role_still_gets_403_on_list(client: AsyncClient):
    """Regular user role is still forbidden from GET /admin/projects."""
    await _create_user("plain_test", role="user")
    await client.post("/auth/login", json={"login_id": "plain_test", "password": "pass123"})
    resp = await client.get("/admin/projects")
    assert resp.status_code == 403


# ---------------------------------------------------------------------------
# project_admin role — GET /admin/projects/{id}/members
# ---------------------------------------------------------------------------


async def test_project_admin_can_view_members_of_own_project(
    admin_client: AsyncClient,
    project_admin_client: AsyncClient,
):
    """project_admin that is a member can list members of that project."""
    admin_resp = await admin_client.get("/auth/me")
    admin_id = admin_resp.json()["data"]["id"]
    await _create_project("pa_mbr", "Member Project", admin_id)

    padmin_resp = await project_admin_client.get("/auth/me")
    padmin_id = padmin_resp.json()["data"]["id"]
    await admin_client.post("/admin/projects/pa_mbr/members", json={"user_id": padmin_id, "role": "member"})

    resp = await project_admin_client.get("/admin/projects/pa_mbr/members")
    assert resp.status_code == 200
    user_ids = [m["user_id"] for m in resp.json()["data"]]
    assert padmin_id in user_ids


async def test_project_admin_cannot_view_members_of_other_project(
    admin_client: AsyncClient,
    project_admin_client: AsyncClient,
):
    """project_admin not in a project gets 403 on member list."""
    admin_resp = await admin_client.get("/auth/me")
    admin_id = admin_resp.json()["data"]["id"]
    await _create_project("pa_mbr2", "Other Members Project", admin_id)

    resp = await project_admin_client.get("/admin/projects/pa_mbr2/members")
    assert resp.status_code == 403


async def test_project_admin_cannot_add_member(
    admin_client: AsyncClient,
    project_admin_client: AsyncClient,
):
    """project_admin cannot add members even to their own project."""
    admin_resp = await admin_client.get("/auth/me")
    admin_id = admin_resp.json()["data"]["id"]
    await _create_project("pa_addmbr", "Add Member Project", admin_id)

    padmin_resp = await project_admin_client.get("/auth/me")
    padmin_id = padmin_resp.json()["data"]["id"]
    await admin_client.post("/admin/projects/pa_addmbr/members", json={"user_id": padmin_id, "role": "member"})

    other_uid = await _create_user("other_add_test")
    resp = await project_admin_client.post(
        "/admin/projects/pa_addmbr/members", json={"user_id": other_uid, "role": "member"}
    )
    assert resp.status_code == 403
