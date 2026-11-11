"""Single admin (env credentials) + project-scoped API keys."""
from datetime import UTC, datetime, timedelta

import pytest
from httpx import AsyncClient

from app.config import settings
from tests.conftest import ADMIN_PASSWORD, bearer, create_key


def _ingest_body(project_id: str | None, name: str = "ingested") -> dict:
    entity = {"type": "FEATURE", "canonical_name": name}
    if project_id:
        entity["project_id"] = project_id
    return {"source": {"type": "test", "name": "t", "uri": "file://t"}, "entities": [entity], "relations": []}


async def _entity(admin_client: AsyncClient, project_id: str | None) -> str:
    body = {"type": "FEATURE", "canonical_name": f"e-{project_id}"}
    if project_id:
        await admin_client.post("/projects", json={"id": project_id, "alias": project_id})
        body["project_id"] = project_id
    resp = await admin_client.post("/entities", json=body)
    assert resp.status_code == 201, resp.text
    return resp.json()["data"]["id"]


# --- admin login -------------------------------------------------------------


async def test_admin_login_success_and_me(client: AsyncClient):
    resp = await client.post("/auth/login", json={"login_id": "admin", "password": ADMIN_PASSWORD})
    assert resp.status_code == 200
    assert "access_token" in resp.cookies
    me = await client.get("/auth/me")
    assert me.status_code == 200
    assert me.json()["data"] == {"login_id": "admin", "role": "admin"}


async def test_admin_login_wrong_password(client: AsyncClient):
    resp = await client.post("/auth/login", json={"login_id": "admin", "password": "nope"})
    assert resp.status_code == 401


async def test_admin_login_disabled_without_password(client: AsyncClient, monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setattr(settings, "admin_password", None)
    resp = await client.post("/auth/login", json={"login_id": "admin", "password": ""})
    assert resp.status_code == 503


async def test_logout_clears_session(admin_client: AsyncClient):
    await admin_client.post("/auth/logout")
    assert (await admin_client.get("/auth/me")).status_code == 401


async def test_me_rejects_api_key(client: AsyncClient, read_key: str):
    assert (await client.get("/auth/me", headers=bearer(read_key))).status_code == 403


# --- key issuance ------------------------------------------------------------


async def test_issue_key_prefixed_and_hidden_in_list(admin_client: AsyncClient, project: str):
    resp = await admin_client.post(
        "/admin/api-keys", json={"name": "agent", "project_id": project, "scope": "write"}
    )
    assert resp.status_code == 201, resp.text
    data = resp.json()["data"]
    assert data["key"].startswith("crr_")
    assert data["scope"] == "write"

    listed = (await admin_client.get("/admin/api-keys")).json()["data"]
    assert len(listed) == 1
    assert "key" not in listed[0] and "key_hash" not in listed[0]
    assert listed[0]["project_id"] == project


async def test_issue_key_requires_existing_project(admin_client: AsyncClient):
    resp = await admin_client.post("/admin/api-keys", json={"name": "x", "project_id": "NOPE"})
    assert resp.status_code == 404
    resp = await admin_client.post("/admin/api-keys", json={"name": "x"})
    assert resp.status_code == 422


async def test_key_management_is_admin_only(client: AsyncClient, write_key: str):
    assert (await client.get("/admin/api-keys")).status_code == 401
    assert (await client.get("/admin/api-keys", headers=bearer(write_key))).status_code == 403


async def test_last_used_at_updated(admin_client: AsyncClient, client: AsyncClient, read_key: str):
    await client.get("/entities", headers=bearer(read_key))
    listed = (await admin_client.get("/admin/api-keys")).json()["data"]
    assert listed[0]["last_used_at"] is not None


# --- scope -------------------------------------------------------------------


async def test_read_key_cannot_ingest(client: AsyncClient, project: str, read_key: str):
    resp = await client.post("/ingest/batch", json=_ingest_body(project), headers=bearer(read_key))
    assert resp.status_code == 403


async def test_write_key_can_ingest(client: AsyncClient, project: str, write_key: str):
    resp = await client.post("/ingest/batch", json=_ingest_body(project), headers=bearer(write_key))
    assert resp.status_code == 200, resp.text


async def test_write_key_cannot_ingest_public(client: AsyncClient, write_key: str):
    resp = await client.post("/ingest/batch", json=_ingest_body(None), headers=bearer(write_key))
    assert resp.status_code == 403


async def test_write_key_cannot_hijack_other_project_entity_via_ingest(
    admin_client: AsyncClient, client: AsyncClient, project: str, write_key: str
):
    other_id = await _entity(admin_client, "OTHER")
    body = _ingest_body(project)
    body["entities"][0]["id"] = other_id
    resp = await client.post("/ingest/batch", json=body, headers=bearer(write_key))
    assert resp.status_code == 403
    assert (await admin_client.get(f"/entities/{other_id}")).json()["data"]["project_id"] == "OTHER"


async def test_write_key_cannot_modify_other_project_or_public(
    admin_client: AsyncClient, client: AsyncClient, write_key: str
):
    other_id = await _entity(admin_client, "OTHER")
    public_id = await _entity(admin_client, None)
    for eid in (other_id, public_id):
        resp = await client.patch(f"/entities/{eid}", json={"canonical_name": "x"}, headers=bearer(write_key))
        assert resp.status_code == 403


async def test_key_view_scope(admin_client: AsyncClient, client: AsyncClient, read_key: str):
    other_id = await _entity(admin_client, "OTHER")
    public_id = await _entity(admin_client, None)
    assert (await client.get(f"/entities/{other_id}", headers=bearer(read_key))).status_code == 403
    assert (await client.get(f"/entities/{public_id}", headers=bearer(read_key))).status_code == 200


# --- key validity ------------------------------------------------------------


async def test_expired_key_rejected(client: AsyncClient, project: str):
    key = await create_key(project, "read", expires_at=datetime.now(UTC) - timedelta(minutes=1))
    assert (await client.get("/entities", headers=bearer(key))).status_code == 401


async def test_future_expiry_accepted(client: AsyncClient, project: str):
    key = await create_key(project, "read", expires_at=datetime.now(UTC) + timedelta(days=1))
    assert (await client.get("/entities", headers=bearer(key))).status_code == 200


async def test_revoked_key_rejected(admin_client: AsyncClient, client: AsyncClient, read_key: str):
    key_id = (await admin_client.get("/admin/api-keys")).json()["data"][0]["id"]
    resp = await admin_client.delete(f"/admin/api-keys/{key_id}")
    assert resp.status_code == 200
    assert resp.json()["data"]["is_active"] is False
    assert (await client.get("/entities", headers=bearer(read_key))).status_code == 401


async def test_x_api_key_header_not_accepted(client: AsyncClient, write_key: str):
    """X-API-Key is ignored: a write call with only that header is unauthenticated."""
    resp = await client.post(
        "/entities", json={"type": "FEATURE", "canonical_name": "x"}, headers={"X-API-Key": write_key}
    )
    assert resp.status_code == 401
