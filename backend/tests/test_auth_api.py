"""Tests for auth endpoints: login/logout/me, user management, API key auth."""
import pytest
from httpx import AsyncClient

from app.service.auth_service import AuthService, hash_password, _hash_api_key
from app.repository.user_repository import UserRepository
from app.repository.api_key_repository import ApiKeyRepository
from app.domain.models import UserAccount, ApiKey
from app.db.session import async_session_factory


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


async def _create_user(
    client: AsyncClient,
    *,
    email: str = "test@example.com",
    password: str = "secret123",
    display_name: str = "Test User",
    role: str = "user",
) -> dict:
    async with async_session_factory() as session:
        svc = AuthService(session)
        user = await svc.create_user(
            email=email,
            password=password,
            display_name=display_name,
            role=role,
        )
    return {"id": str(user.id), "email": user.email}


async def _login(client: AsyncClient, email: str, password: str) -> AsyncClient:
    resp = await client.post("/auth/login", json={"email": email, "password": password})
    assert resp.status_code == 200, resp.text
    return client


# ---------------------------------------------------------------------------
# Login
# ---------------------------------------------------------------------------


async def test_login_success(client: AsyncClient):
    await _create_user(client, email="admin@test.com", password="pass123", role="admin")
    resp = await client.post("/auth/login", json={"email": "admin@test.com", "password": "pass123"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["ok"] is True
    assert data["data"]["email"] == "admin@test.com"
    assert data["data"]["role"] == "admin"
    assert "access_token" in resp.cookies


async def test_login_wrong_password(client: AsyncClient):
    await _create_user(client, email="u@test.com", password="correct")
    resp = await client.post("/auth/login", json={"email": "u@test.com", "password": "wrong"})
    assert resp.status_code == 401
    assert resp.json()["error"]["code"] == "UNAUTHORIZED"


async def test_login_unknown_email(client: AsyncClient):
    resp = await client.post("/auth/login", json={"email": "nope@test.com", "password": "x"})
    assert resp.status_code == 401


async def test_login_inactive_user(client: AsyncClient):
    async with async_session_factory() as session:
        pw_hash = hash_password("pass")
        user = UserAccount(
            email="inactive@test.com",
            password_hash=pw_hash,
            display_name="Inactive",
            role="user",
            is_active=False,
        )
        session.add(user)
        await session.commit()

    resp = await client.post("/auth/login", json={"email": "inactive@test.com", "password": "pass"})
    assert resp.status_code == 401


async def test_login_email_case_insensitive(client: AsyncClient):
    await _create_user(client, email="Upper@Test.COM", password="pw")
    resp = await client.post("/auth/login", json={"email": "upper@test.com", "password": "pw"})
    assert resp.status_code == 200


# ---------------------------------------------------------------------------
# Logout
# ---------------------------------------------------------------------------


async def test_logout(client: AsyncClient):
    await _create_user(client, email="u@test.com", password="pw")
    await _login(client, "u@test.com", "pw")

    resp = await client.post("/auth/logout")
    assert resp.status_code == 200
    assert resp.json()["ok"] is True

    # after logout cookie is cleared — /auth/me should fail
    resp2 = await client.get("/auth/me")
    assert resp2.status_code == 401


# ---------------------------------------------------------------------------
# /auth/me
# ---------------------------------------------------------------------------


async def test_me_authenticated(client: AsyncClient):
    await _create_user(client, email="me@test.com", password="pw")
    await _login(client, "me@test.com", "pw")
    resp = await client.get("/auth/me")
    assert resp.status_code == 200
    assert resp.json()["data"]["email"] == "me@test.com"


async def test_me_unauthenticated(client: AsyncClient):
    resp = await client.get("/auth/me")
    assert resp.status_code == 401


# ---------------------------------------------------------------------------
# User management (admin only)
# ---------------------------------------------------------------------------


async def test_admin_can_create_user(client: AsyncClient):
    await _create_user(client, email="admin@test.com", password="pw", role="admin")
    await _login(client, "admin@test.com", "pw")

    resp = await client.post("/auth/users", json={
        "email": "newuser@test.com",
        "password": "pw123",
        "display_name": "New User",
        "role": "user",
    })
    assert resp.status_code == 201
    assert resp.json()["data"]["email"] == "newuser@test.com"


async def test_non_admin_cannot_create_user(client: AsyncClient):
    await _create_user(client, email="user@test.com", password="pw", role="user")
    await _login(client, "user@test.com", "pw")

    resp = await client.post("/auth/users", json={
        "email": "other@test.com",
        "password": "pw",
        "display_name": "Other",
    })
    assert resp.status_code == 403


async def test_duplicate_email_rejected(client: AsyncClient):
    await _create_user(client, email="admin@test.com", password="pw", role="admin")
    await _login(client, "admin@test.com", "pw")

    await client.post("/auth/users", json={
        "email": "dup@test.com", "password": "pw", "display_name": "A",
    })
    resp = await client.post("/auth/users", json={
        "email": "dup@test.com", "password": "pw", "display_name": "B",
    })
    assert resp.status_code == 409


# ---------------------------------------------------------------------------
# API Key auth (Step 2-1-3)
# ---------------------------------------------------------------------------


async def test_api_key_auth_success(client: AsyncClient):
    await _create_user(client, email="admin@test.com", password="pw", role="admin")
    await _login(client, "admin@test.com", "pw")

    resp = await client.post("/auth/api-keys", json={
        "name": "test-key",
        "scopes": ["read", "write"],
    })
    assert resp.status_code == 201
    raw_key = resp.json()["data"]["key"]

    # log out cookie session
    await client.post("/auth/logout")

    # API key auth still works: /auth/me returns the key owner
    resp2 = await client.get("/auth/me", headers={"Authorization": f"Bearer {raw_key}"})
    assert resp2.status_code == 200
    assert resp2.json()["data"]["email"] == "admin@test.com"


async def test_api_key_x_api_key_header(client: AsyncClient):
    await _create_user(client, email="admin@test.com", password="pw", role="admin")
    await _login(client, "admin@test.com", "pw")

    resp = await client.post("/auth/api-keys", json={"name": "test-key", "scopes": ["read"]})
    assert resp.status_code == 201
    raw_key = resp.json()["data"]["key"]

    await client.post("/auth/logout")

    # X-API-Key header works the same as Authorization: Bearer
    resp2 = await client.get("/auth/me", headers={"X-API-Key": raw_key})
    assert resp2.status_code == 200
    assert resp2.json()["data"]["email"] == "admin@test.com"


async def test_api_key_invalid(client: AsyncClient):
    resp = await client.get("/health")  # just checking health still works
    assert resp.status_code == 200

    # Invalid API key on a protected endpoint
    resp2 = await client.get("/auth/me", headers={"Authorization": "Bearer invalid-key-xxx"})
    assert resp2.status_code == 401


async def test_api_key_admin_creates_key(client: AsyncClient):
    await _create_user(client, email="admin@test.com", password="pw", role="admin")
    await _login(client, "admin@test.com", "pw")

    resp = await client.post("/auth/api-keys", json={
        "name": "ingest-key",
        "scopes": ["ingest"],
    })
    assert resp.status_code == 201
    body = resp.json()["data"]
    assert body["name"] == "ingest-key"
    assert "ingest" in body["scopes"]
    assert len(body["key"]) > 20  # raw key returned


async def test_regular_user_can_create_api_key(client: AsyncClient):
    # Regular users can create API keys, but project_id is required
    user = await _create_user(client, email="user@test.com", password="pw", role="user")
    await _login(client, "user@test.com", "pw")

    # Create project and add user as member via service layer
    from app.service.project_service import ProjectService
    from app.repository.project_member_repository import ProjectMemberRepository
    import uuid as _uuid
    async with async_session_factory() as session:
        admin = await AuthService(session).create_user(
            email="admin-helper@test.com", password="pw", display_name="A", role="admin"
        )
        await ProjectService(session).create_project(
            id="user-proj", alias="User Project", description=None, created_by=admin.id
        )
        await ProjectMemberRepository(session).create(
            project_id="user-proj",
            user_id=_uuid.UUID(user["id"]),
            role="editor",
            created_by=admin.id,
        )
        await session.commit()

    resp = await client.post("/auth/api-keys", json={"name": "key", "scopes": ["read:entities"], "project_id": "user-proj"})
    assert resp.status_code == 201
    assert resp.json()["data"]["name"] == "key"


# ---------------------------------------------------------------------------
# Password not stored in plain text
# ---------------------------------------------------------------------------


async def test_password_not_plain(client: AsyncClient):
    await _create_user(client, email="u@test.com", password="mysecret")
    async with async_session_factory() as session:
        user = await UserRepository(session).get_by_email("u@test.com")
    assert user is not None
    assert user.password_hash != "mysecret"
    assert user.password_hash.startswith("$argon2")
