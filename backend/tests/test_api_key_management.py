"""Tests for API key management: list, create, revoke (user + admin flows)."""
import pytest
from httpx import AsyncClient

from app.db.session import async_session_factory
from app.service.auth_service import AuthService


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


async def _create_user_and_login(
    client: AsyncClient,
    *,
    email: str,
    password: str = "pass123",
    display_name: str = "Test",
    role: str = "user",
) -> AsyncClient:
    async with async_session_factory() as session:
        await AuthService(session).create_user(
            email=email,
            password=password,
            display_name=display_name,
            role=role,
        )
    resp = await client.post("/auth/login", json={"email": email, "password": password})
    assert resp.status_code == 200, resp.text
    return client


# ---------------------------------------------------------------------------
# User: create API key
# ---------------------------------------------------------------------------


async def test_user_can_create_api_key(client: AsyncClient):
    await _create_user_and_login(client, email="user@test.com")
    resp = await client.post(
        "/auth/api-keys",
        json={"name": "my-key", "scopes": ["read:entities"]},
    )
    assert resp.status_code == 201, resp.text
    data = resp.json()["data"]
    assert data["name"] == "my-key"
    assert "key" in data
    assert data["key"].startswith("") and len(data["key"]) > 20


# ---------------------------------------------------------------------------
# User: list API keys
# ---------------------------------------------------------------------------


async def test_user_list_api_keys_empty(client: AsyncClient):
    await _create_user_and_login(client, email="user@test.com")
    resp = await client.get("/auth/api-keys")
    assert resp.status_code == 200
    assert resp.json()["data"] == []


async def test_user_list_api_keys_returns_own_keys(client: AsyncClient):
    await _create_user_and_login(client, email="user@test.com")
    await client.post("/auth/api-keys", json={"name": "key1", "scopes": ["read:entities"]})
    await client.post("/auth/api-keys", json={"name": "key2", "scopes": ["ingest"]})

    resp = await client.get("/auth/api-keys")
    assert resp.status_code == 200
    keys = resp.json()["data"]
    assert len(keys) == 2
    names = {k["name"] for k in keys}
    assert names == {"key1", "key2"}


async def test_user_cannot_see_other_users_keys(client: AsyncClient):
    """Two separate clients; each should only see their own keys."""
    async with AsyncClient(
        transport=client._transport, base_url="http://test"
    ) as other:
        await _create_user_and_login(client, email="alice@test.com")
        await _create_user_and_login(other, email="bob@test.com")

        await client.post("/auth/api-keys", json={"name": "alice-key", "scopes": ["read:entities"]})
        await other.post("/auth/api-keys", json={"name": "bob-key", "scopes": ["read:entities"]})

        alice_keys = (await client.get("/auth/api-keys")).json()["data"]
        bob_keys = (await other.get("/auth/api-keys")).json()["data"]

        assert all(k["name"] == "alice-key" for k in alice_keys)
        assert all(k["name"] == "bob-key" for k in bob_keys)


# ---------------------------------------------------------------------------
# User: revoke own key
# ---------------------------------------------------------------------------


async def test_user_revoke_own_key(client: AsyncClient):
    await _create_user_and_login(client, email="user@test.com")
    create_resp = await client.post(
        "/auth/api-keys", json={"name": "to-revoke", "scopes": ["read:entities"]}
    )
    key_id = create_resp.json()["data"]["id"]

    revoke_resp = await client.delete(f"/auth/api-keys/{key_id}")
    assert revoke_resp.status_code == 200
    data = revoke_resp.json()["data"]
    assert data["is_active"] is False
    assert data["revoked_at"] is not None


async def test_revoked_key_shows_inactive_in_list(client: AsyncClient):
    await _create_user_and_login(client, email="user@test.com")
    create_resp = await client.post(
        "/auth/api-keys", json={"name": "key", "scopes": ["read:entities"]}
    )
    key_id = create_resp.json()["data"]["id"]
    await client.delete(f"/auth/api-keys/{key_id}")

    keys = (await client.get("/auth/api-keys")).json()["data"]
    assert len(keys) == 1
    assert keys[0]["is_active"] is False


# ---------------------------------------------------------------------------
# User: cannot revoke another user's key
# ---------------------------------------------------------------------------


async def test_user_cannot_revoke_others_key(client: AsyncClient):
    from httpx import AsyncClient as AClient, ASGITransport
    from app.main import app

    async with AClient(transport=ASGITransport(app=app), base_url="http://test") as other:
        await _create_user_and_login(client, email="alice@test.com")
        await _create_user_and_login(other, email="bob@test.com")

        create_resp = await other.post(
            "/auth/api-keys", json={"name": "bob-key", "scopes": ["read:entities"]}
        )
        bob_key_id = create_resp.json()["data"]["id"]

        # Alice tries to revoke Bob's key
        resp = await client.delete(f"/auth/api-keys/{bob_key_id}")
        assert resp.status_code == 403


# ---------------------------------------------------------------------------
# Admin: list all API keys
# ---------------------------------------------------------------------------


async def test_admin_list_all_api_keys(admin_client: AsyncClient, client: AsyncClient):
    await _create_user_and_login(client, email="user@test.com")
    await client.post("/auth/api-keys", json={"name": "user-key", "scopes": ["read:entities"]})
    await admin_client.post("/auth/api-keys", json={"name": "admin-key", "scopes": ["read:all"]})

    resp = await admin_client.get("/admin/api-keys")
    assert resp.status_code == 200
    keys = resp.json()["data"]
    assert len(keys) == 2
    assert any(k["name"] == "user-key" for k in keys)
    assert any(k["name"] == "admin-key" for k in keys)
    # All entries should have created_by_email field
    for k in keys:
        assert "created_by_email" in k


async def test_admin_list_api_keys_filter_active(admin_client: AsyncClient):
    create_resp = await admin_client.post(
        "/auth/api-keys", json={"name": "active-key", "scopes": ["read:entities"]}
    )
    key_id = create_resp.json()["data"]["id"]
    await admin_client.post("/auth/api-keys", json={"name": "will-revoke", "scopes": ["read:entities"]})
    revoke_resp = await admin_client.post(
        "/auth/api-keys", json={"name": "revoked", "scopes": ["read:entities"]}
    )
    revoked_id = revoke_resp.json()["data"]["id"]
    await admin_client.delete(f"/auth/api-keys/{revoked_id}")

    active_resp = await admin_client.get("/admin/api-keys?is_active=true")
    active_keys = active_resp.json()["data"]
    assert all(k["is_active"] for k in active_keys)

    inactive_resp = await admin_client.get("/admin/api-keys?is_active=false")
    inactive_keys = inactive_resp.json()["data"]
    assert all(not k["is_active"] for k in inactive_keys)


# ---------------------------------------------------------------------------
# Admin: revoke any key
# ---------------------------------------------------------------------------


async def test_admin_can_revoke_others_key(admin_client: AsyncClient, client: AsyncClient):
    await _create_user_and_login(client, email="user@test.com")
    create_resp = await client.post(
        "/auth/api-keys", json={"name": "user-key", "scopes": ["read:entities"]}
    )
    key_id = create_resp.json()["data"]["id"]

    resp = await admin_client.delete(f"/admin/api-keys/{key_id}")
    assert resp.status_code == 200
    assert resp.json()["data"]["is_active"] is False


# ---------------------------------------------------------------------------
# Non-admin cannot access /admin/api-keys
# ---------------------------------------------------------------------------


async def test_non_admin_cannot_list_all_keys(client: AsyncClient):
    await _create_user_and_login(client, email="user@test.com")
    resp = await client.get("/admin/api-keys")
    assert resp.status_code == 403


async def test_unauthenticated_cannot_list_keys(client: AsyncClient):
    resp = await client.get("/auth/api-keys")
    assert resp.status_code == 401
