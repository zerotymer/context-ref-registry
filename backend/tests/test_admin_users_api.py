"""Tests for /admin/users endpoints."""
import pytest
from httpx import AsyncClient

from app.db.session import async_session_factory
from app.service.auth_service import AuthService


async def _create_user_direct(login_id: str, password: str, role: str = "user") -> str:
    async with async_session_factory() as session:
        svc = AuthService(session)
        user = await svc.create_user(login_id=login_id, password=password, display_name=login_id, role=role)
    return str(user.id)


# ---------------------------------------------------------------------------
# GET /admin/users
# ---------------------------------------------------------------------------


async def test_list_users_admin_only(client: AsyncClient, admin_client: AsyncClient):
    await _create_user_direct("user1", "pass")
    await _create_user_direct("user2", "pass")

    resp = await admin_client.get("/admin/users")
    assert resp.status_code == 200
    data = resp.json()["data"]
    assert len(data) >= 3  # admin + user1 + user2


async def test_list_users_forbidden_for_non_admin(client: AsyncClient):
    await _create_user_direct("plain_user", "pass", role="user")
    resp = await client.post("/auth/login", json={"login_id": "plain_user", "password": "pass"})
    assert resp.status_code == 200

    resp = await client.get("/admin/users")
    assert resp.status_code == 403


async def test_list_users_filter_role(admin_client: AsyncClient):
    await _create_user_direct("proj_admin_user", "pass", role="project_admin")
    await _create_user_direct("reg_user", "pass", role="user")

    resp = await admin_client.get("/admin/users?role=project_admin")
    assert resp.status_code == 200
    data = resp.json()["data"]
    assert all(u["role"] == "project_admin" for u in data)


async def test_list_users_filter_is_active(admin_client: AsyncClient):
    uid = await _create_user_direct("inactive_user", "pass", role="user")
    await admin_client.patch(f"/admin/users/{uid}", json={"is_active": False})

    resp = await admin_client.get("/admin/users?is_active=false")
    assert resp.status_code == 200
    data = resp.json()["data"]
    assert all(not u["is_active"] for u in data)


async def test_list_users_search_login_id(admin_client: AsyncClient):
    await _create_user_direct("alice_example", "pass")
    await _create_user_direct("bob_other", "pass")

    resp = await admin_client.get("/admin/users?search=example")
    assert resp.status_code == 200
    data = resp.json()["data"]
    assert all("example" in u["login_id"] for u in data)


# ---------------------------------------------------------------------------
# POST /admin/users
# ---------------------------------------------------------------------------


async def test_create_user(admin_client: AsyncClient):
    resp = await admin_client.post("/admin/users", json={
        "login_id": "new_user",
        "password": "password123",
        "display_name": "New User",
        "role": "user",
    })
    assert resp.status_code == 201
    data = resp.json()["data"]
    assert data["login_id"] == "new_user"
    assert data["role"] == "user"
    assert data["is_active"] is True


async def test_create_user_conflict(admin_client: AsyncClient):
    await _create_user_direct("dup_user", "pass")
    resp = await admin_client.post("/admin/users", json={
        "login_id": "dup_user",
        "password": "pass2",
        "display_name": "Dup",
    })
    assert resp.status_code == 409


async def test_create_user_non_admin_forbidden(client: AsyncClient):
    await _create_user_direct("plain_user", "pass")
    await client.post("/auth/login", json={"login_id": "plain_user", "password": "pass"})

    resp = await client.post("/admin/users", json={
        "login_id": "new_user",
        "password": "pass",
        "display_name": "X",
    })
    assert resp.status_code == 403


# ---------------------------------------------------------------------------
# PATCH /admin/users/{user_id}
# ---------------------------------------------------------------------------


async def test_update_user_role(admin_client: AsyncClient):
    uid = await _create_user_direct("promo_user", "pass", role="user")

    resp = await admin_client.patch(f"/admin/users/{uid}", json={"role": "project_admin"})
    assert resp.status_code == 200
    assert resp.json()["data"]["role"] == "project_admin"


async def test_update_user_deactivate(admin_client: AsyncClient):
    uid = await _create_user_direct("deact_user", "pass")

    resp = await admin_client.patch(f"/admin/users/{uid}", json={"is_active": False})
    assert resp.status_code == 200
    assert resp.json()["data"]["is_active"] is False


async def test_deactivated_user_cannot_login(admin_client: AsyncClient, client: AsyncClient):
    uid = await _create_user_direct("blocked_user", "pass")
    await admin_client.patch(f"/admin/users/{uid}", json={"is_active": False})

    resp = await client.post("/auth/login", json={"login_id": "blocked_user", "password": "pass"})
    assert resp.status_code == 401


async def test_update_user_invalid_role(admin_client: AsyncClient):
    uid = await _create_user_direct("role_user", "pass")
    resp = await admin_client.patch(f"/admin/users/{uid}", json={"role": "superuser"})
    assert resp.status_code == 422


async def test_update_user_not_found(admin_client: AsyncClient):
    import uuid
    resp = await admin_client.patch(f"/admin/users/{uuid.uuid4()}", json={"role": "user"})
    assert resp.status_code == 404


# ---------------------------------------------------------------------------
# POST /admin/users/{user_id}/reset-password
# ---------------------------------------------------------------------------


async def test_reset_password(admin_client: AsyncClient, client: AsyncClient):
    uid = await _create_user_direct("reset_user", "old_pass")

    resp = await admin_client.post(f"/admin/users/{uid}/reset-password", json={"new_password": "new_pass123"})
    assert resp.status_code == 200

    login = await client.post("/auth/login", json={"login_id": "reset_user", "password": "new_pass123"})
    assert login.status_code == 200

    old_login = await client.post("/auth/login", json={"login_id": "reset_user", "password": "old_pass"})
    assert old_login.status_code == 401


async def test_reset_password_not_found(admin_client: AsyncClient):
    import uuid
    resp = await admin_client.post(f"/admin/users/{uuid.uuid4()}/reset-password", json={"new_password": "x"})
    assert resp.status_code == 404
