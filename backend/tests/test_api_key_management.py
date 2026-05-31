"""Tests for API key management: list, create, revoke (user + admin flows)."""
import pytest
import uuid
from httpx import AsyncClient

from app.db.session import async_session_factory
from app.service.auth_service import AuthService
from app.service.project_service import ProjectService
from app.repository.project_member_repository import ProjectMemberRepository


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


async def _create_user_and_login(
    client: AsyncClient,
    *,
    login_id: str,
    password: str = "pass123",
    display_name: str = "Test",
    role: str = "user",
) -> dict:
    async with async_session_factory() as session:
        user = await AuthService(session).create_user(
            login_id=login_id,
            password=password,
            display_name=display_name,
            role=role,
        )
    resp = await client.post("/auth/login", json={"login_id": login_id, "password": password})
    assert resp.status_code == 200, resp.text
    return {"id": str(user.id)}


async def _create_project_with_member(user_id: str, project_id: str = "test_proj") -> str:
    """Create a project as admin and add user as member. Returns project_id."""
    async with async_session_factory() as session:
        admin = await AuthService(session).create_user(
            login_id=f"proj_admin_{project_id}",
            password="pw",
            display_name="Proj Admin",
            role="admin",
        )
        await ProjectService(session).create_project(
            id=project_id,
            alias=project_id,
            description=None,
            created_by=admin.id,
        )
        await ProjectMemberRepository(session).create(
            project_id=project_id,
            user_id=uuid.UUID(user_id),
            role="editor",
            created_by=admin.id,
        )
        await session.commit()
    return project_id


# ---------------------------------------------------------------------------
# User: create API key (project_id now required for non-admin)
# ---------------------------------------------------------------------------


async def test_user_can_create_api_key(client: AsyncClient):
    user = await _create_user_and_login(client, login_id="user_test")
    proj_id = await _create_project_with_member(user["id"])

    resp = await client.post(
        "/auth/api-keys",
        json={"name": "my-key", "scopes": ["read:entities"], "project_id": proj_id},
    )
    assert resp.status_code == 201, resp.text
    data = resp.json()["data"]
    assert data["name"] == "my-key"
    assert "key" in data
    assert data["key"].startswith("") and len(data["key"]) > 20


async def test_user_requires_project_id(client: AsyncClient):
    """Regular user without project_id gets 422."""
    await _create_user_and_login(client, login_id="user_test")
    resp = await client.post(
        "/auth/api-keys",
        json={"name": "my-key", "scopes": ["read:entities"]},
    )
    assert resp.status_code == 422
    assert resp.json()["error"]["code"] == "PROJECT_REQUIRED"


async def test_user_nonmember_project_gets_403(client: AsyncClient):
    """Regular user trying to create key for a project they're not member of."""
    await _create_user_and_login(client, login_id="user_test")
    async with async_session_factory() as session:
        admin = await AuthService(session).create_user(
            login_id="admin_other", password="pw", display_name="A", role="admin"
        )
        await ProjectService(session).create_project(
            id="other_proj", alias="Other", description=None, created_by=admin.id
        )
    resp = await client.post(
        "/auth/api-keys",
        json={"name": "k", "scopes": ["read:entities"], "project_id": "other_proj"},
    )
    assert resp.status_code == 403


async def test_user_member_project_success(client: AsyncClient):
    """Regular user creates key for a project they ARE a member of."""
    user = await _create_user_and_login(client, login_id="user_test")
    proj_id = await _create_project_with_member(user["id"], "member_proj")
    resp = await client.post(
        "/auth/api-keys",
        json={"name": "k", "scopes": ["read:entities"], "project_id": proj_id},
    )
    assert resp.status_code == 201
    data = resp.json()["data"]
    assert data["name"] == "k"


# ---------------------------------------------------------------------------
# User: list API keys
# ---------------------------------------------------------------------------


async def test_user_list_api_keys_empty(client: AsyncClient):
    await _create_user_and_login(client, login_id="user_test")
    resp = await client.get("/auth/api-keys")
    assert resp.status_code == 200
    assert resp.json()["data"] == []


async def test_user_list_api_keys_returns_own_keys(client: AsyncClient):
    user = await _create_user_and_login(client, login_id="user_test")
    proj_id = await _create_project_with_member(user["id"])
    await client.post("/auth/api-keys", json={"name": "key1", "scopes": ["read:entities"], "project_id": proj_id})
    await client.post("/auth/api-keys", json={"name": "key2", "scopes": ["ingest"], "project_id": proj_id})

    resp = await client.get("/auth/api-keys")
    assert resp.status_code == 200
    keys = resp.json()["data"]
    assert len(keys) == 2
    names = {k["name"] for k in keys}
    assert names == {"key1", "key2"}
    for k in keys:
        assert "project_name" in k
        assert "is_legacy" in k
        assert k["is_legacy"] is False


async def test_user_cannot_see_other_users_keys(client: AsyncClient):
    """Two separate clients; each should only see their own keys."""
    from httpx import AsyncClient as AClient, ASGITransport
    from app.main import app

    async with AClient(transport=ASGITransport(app=app), base_url="http://test") as other:
        alice = await _create_user_and_login(client, login_id="alice_test")
        bob = await _create_user_and_login(other, login_id="bob_test")

        alice_proj = await _create_project_with_member(alice["id"], "alice_proj")
        bob_proj = await _create_project_with_member(bob["id"], "bob_proj")

        await client.post("/auth/api-keys", json={"name": "alice-key", "scopes": ["read:entities"], "project_id": alice_proj})
        await other.post("/auth/api-keys", json={"name": "bob-key", "scopes": ["read:entities"], "project_id": bob_proj})

        alice_keys = (await client.get("/auth/api-keys")).json()["data"]
        bob_keys = (await other.get("/auth/api-keys")).json()["data"]

        assert all(k["name"] == "alice-key" for k in alice_keys)
        assert all(k["name"] == "bob-key" for k in bob_keys)


# ---------------------------------------------------------------------------
# User: revoke own key
# ---------------------------------------------------------------------------


async def test_user_revoke_own_key(client: AsyncClient):
    user = await _create_user_and_login(client, login_id="user_test")
    proj_id = await _create_project_with_member(user["id"])
    create_resp = await client.post(
        "/auth/api-keys", json={"name": "to-revoke", "scopes": ["read:entities"], "project_id": proj_id}
    )
    key_id = create_resp.json()["data"]["id"]

    revoke_resp = await client.delete(f"/auth/api-keys/{key_id}")
    assert revoke_resp.status_code == 200
    data = revoke_resp.json()["data"]
    assert data["is_active"] is False
    assert data["revoked_at"] is not None


async def test_revoked_key_shows_inactive_in_list(client: AsyncClient):
    user = await _create_user_and_login(client, login_id="user_test")
    proj_id = await _create_project_with_member(user["id"])
    create_resp = await client.post(
        "/auth/api-keys", json={"name": "key", "scopes": ["read:entities"], "project_id": proj_id}
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
        alice = await _create_user_and_login(client, login_id="alice_test")
        bob = await _create_user_and_login(other, login_id="bob_test")

        bob_proj = await _create_project_with_member(bob["id"], "bob_proj2")
        create_resp = await other.post(
            "/auth/api-keys", json={"name": "bob-key", "scopes": ["read:entities"], "project_id": bob_proj}
        )
        bob_key_id = create_resp.json()["data"]["id"]

        # Alice tries to revoke Bob's key
        resp = await client.delete(f"/auth/api-keys/{bob_key_id}")
        assert resp.status_code == 403


# ---------------------------------------------------------------------------
# Admin: list all API keys
# ---------------------------------------------------------------------------


async def test_admin_list_all_api_keys(admin_client: AsyncClient, client: AsyncClient):
    user = await _create_user_and_login(client, login_id="user_test")
    proj_id = await _create_project_with_member(user["id"])
    await client.post("/auth/api-keys", json={"name": "user-key", "scopes": ["read:entities"], "project_id": proj_id})
    await admin_client.post("/auth/api-keys", json={"name": "admin-key", "scopes": ["read:all"]})

    resp = await admin_client.get("/admin/api-keys")
    assert resp.status_code == 200
    keys = resp.json()["data"]
    assert len(keys) == 2
    assert any(k["name"] == "user-key" for k in keys)
    assert any(k["name"] == "admin-key" for k in keys)
    for k in keys:
        assert "created_by_login_id" in k
        assert "project_name" in k
        assert "is_legacy" in k


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
    user = await _create_user_and_login(client, login_id="user_test")
    proj_id = await _create_project_with_member(user["id"])
    create_resp = await client.post(
        "/auth/api-keys", json={"name": "user-key", "scopes": ["read:entities"], "project_id": proj_id}
    )
    key_id = create_resp.json()["data"]["id"]

    resp = await admin_client.delete(f"/admin/api-keys/{key_id}")
    assert resp.status_code == 200
    assert resp.json()["data"]["is_active"] is False


# ---------------------------------------------------------------------------
# Non-admin cannot access /admin/api-keys
# ---------------------------------------------------------------------------


async def test_non_admin_cannot_list_all_keys(client: AsyncClient):
    await _create_user_and_login(client, login_id="user_test")
    resp = await client.get("/admin/api-keys")
    assert resp.status_code == 403


async def test_unauthenticated_cannot_list_keys(client: AsyncClient):
    resp = await client.get("/auth/api-keys")
    assert resp.status_code == 401


# ---------------------------------------------------------------------------
# Project key: access control enforcement
# ---------------------------------------------------------------------------


async def test_project_key_accesses_own_project_entity(admin_client: AsyncClient):
    """A project-scoped API key can read entities in its project."""
    await admin_client.post("/projects", json={"id": "proj_a", "alias": "Project A"})
    await admin_client.post("/ingest/batch", json={
        "source": {"type": "screen_spec", "name": "t", "uri": "file://t", "version": "1"},
        "entities": [{"type": "FEATURE", "canonical_name": "feat-a", "status": "active", "project_id": "proj_a"}],
        "relations": [],
    })
    ent_resp = await admin_client.get("/entities?limit=1")
    entity_id = ent_resp.json()["data"]["items"][0]["id"]

    key_resp = await admin_client.post("/admin/api-keys", json={
        "name": "proj_a_key", "scopes": ["read:entities"], "project_id": "proj_a"
    })
    raw_key = key_resp.json()["data"]["key"]

    from httpx import AsyncClient as AClient, ASGITransport
    from app.main import app
    async with AClient(transport=ASGITransport(app=app), base_url="http://test") as key_client:
        resp = await key_client.get(f"/entities/{entity_id}", headers={"X-API-Key": raw_key})
        assert resp.status_code == 200


async def test_project_key_blocked_from_other_project_entity(admin_client: AsyncClient):
    """A project-scoped API key cannot read entities from another project."""
    await admin_client.post("/projects", json={"id": "proj_b", "alias": "B"})
    await admin_client.post("/projects", json={"id": "proj_c", "alias": "C"})
    await admin_client.post("/ingest/batch", json={
        "source": {"type": "screen_spec", "name": "t", "uri": "file://t2", "version": "1"},
        "entities": [{"type": "FEATURE", "canonical_name": "feat-c", "status": "active", "project_id": "proj_c"}],
        "relations": [],
    })
    ent_resp = await admin_client.get("/entities?limit=1")
    entity_id = ent_resp.json()["data"]["items"][0]["id"]

    key_resp = await admin_client.post("/admin/api-keys", json={
        "name": "proj_b_key", "scopes": ["read:entities"], "project_id": "proj_b"
    })
    raw_key = key_resp.json()["data"]["key"]

    from httpx import AsyncClient as AClient, ASGITransport
    from app.main import app
    async with AClient(transport=ASGITransport(app=app), base_url="http://test") as key_client:
        resp = await key_client.get(f"/entities/{entity_id}", headers={"X-API-Key": raw_key})
        assert resp.status_code == 403


async def test_admin_global_key_accesses_all_projects(admin_client: AsyncClient):
    """A global admin key (project_id=null) can access all project entities."""
    await admin_client.post("/projects", json={"id": "proj_d", "alias": "D"})
    await admin_client.post("/ingest/batch", json={
        "source": {"type": "screen_spec", "name": "t", "uri": "file://t3", "version": "1"},
        "entities": [{"type": "FEATURE", "canonical_name": "feat-d", "status": "active", "project_id": "proj_d"}],
        "relations": [],
    })
    ent_resp = await admin_client.get("/entities?limit=1")
    entity_id = ent_resp.json()["data"]["items"][0]["id"]

    key_resp = await admin_client.post("/admin/api-keys", json={
        "name": "global-key", "scopes": ["read:entities"]
    })
    raw_key = key_resp.json()["data"]["key"]

    from httpx import AsyncClient as AClient, ASGITransport
    from app.main import app
    async with AClient(transport=ASGITransport(app=app), base_url="http://test") as key_client:
        resp = await key_client.get(f"/entities/{entity_id}", headers={"X-API-Key": raw_key})
        assert resp.status_code == 200


async def test_legacy_key_blocked_from_entities(admin_client: AsyncClient):
    """A legacy key (project_id=null, non-admin owner) has no access."""
    from app.db.session import async_session_factory
    from app.repository.api_key_repository import ApiKeyRepository
    import hashlib, secrets

    async with async_session_factory() as session:
        user = await AuthService(session).create_user(
            login_id="legacy_user", password="pw", display_name="Legacy", role="user"
        )
        raw_key = secrets.token_urlsafe(32)
        key_hash = hashlib.sha256(raw_key.encode()).hexdigest()
        await ApiKeyRepository(session).create(
            name="legacy-key", key_hash=key_hash, scopes=["read:entities"],
            project_id=None, created_by=user.id
        )
        await session.commit()

    await admin_client.post("/projects", json={"id": "proj_e", "alias": "E"})
    await admin_client.post("/ingest/batch", json={
        "source": {"type": "screen_spec", "name": "t", "uri": "file://t4", "version": "1"},
        "entities": [{"type": "FEATURE", "canonical_name": "feat-e", "status": "active", "project_id": "proj_e"}],
        "relations": [],
    })
    ent_resp = await admin_client.get("/entities?limit=1")
    entity_id = ent_resp.json()["data"]["items"][0]["id"]

    from httpx import AsyncClient as AClient, ASGITransport
    from app.main import app
    async with AClient(transport=ASGITransport(app=app), base_url="http://test") as key_client:
        resp = await key_client.get(f"/entities/{entity_id}", headers={"X-API-Key": raw_key})
        assert resp.status_code == 403
