import pytest
from httpx import AsyncClient


@pytest.fixture
async def entity_id(admin_client: AsyncClient) -> str:
    resp = await admin_client.post(
        "/entities",
        json={"type": "FEATURE", "canonical_name": "alias 비활성화 테스트 entity"},
    )
    assert resp.status_code == 201
    return resp.json()["data"]["id"]


async def _add_alias(client: AsyncClient, entity_id: str, alias: str) -> str:
    resp = await client.post(
        f"/entities/{entity_id}/aliases",
        json={"locale": "ko", "alias": alias},
    )
    assert resp.status_code == 201
    return resp.json()["data"]["id"]


class TestAliasDeactivate:
    async def test_deactivate_alias(self, admin_client: AsyncClient, entity_id: str):
        alias_id = await _add_alias(admin_client, entity_id, "비활성화할alias")

        resp = await admin_client.delete(f"/entities/{entity_id}/aliases/{alias_id}")
        assert resp.status_code == 200
        data = resp.json()["data"]
        assert data["id"] == alias_id
        assert data["is_active"] is False

    async def test_deactivated_alias_not_in_list(self, admin_client: AsyncClient, entity_id: str):
        alias_id = await _add_alias(admin_client, entity_id, "목록에서 사라질alias")

        await admin_client.delete(f"/entities/{entity_id}/aliases/{alias_id}")

        resp = await admin_client.get(f"/entities/{entity_id}/aliases")
        assert resp.status_code == 200
        ids = [a["id"] for a in resp.json()["data"]]
        assert alias_id not in ids

    async def test_deactivated_alias_not_resolved(self, admin_client: AsyncClient, entity_id: str):
        alias_id = await _add_alias(admin_client, entity_id, "resolve안될alias")
        await admin_client.delete(f"/entities/{entity_id}/aliases/{alias_id}")

        resp = await admin_client.get("/resolve", params={"alias": "resolve안될alias"})
        assert resp.status_code == 200
        assert resp.json()["data"]["result"] == "not_found"

    async def test_deactivate_nonexistent_alias_returns_404(
        self, admin_client: AsyncClient, entity_id: str
    ):
        fake_id = "00000000-0000-0000-0000-000000000000"
        resp = await admin_client.delete(f"/entities/{entity_id}/aliases/{fake_id}")
        assert resp.status_code == 404

    async def test_deactivate_already_inactive_returns_404(
        self, admin_client: AsyncClient, entity_id: str
    ):
        alias_id = await _add_alias(admin_client, entity_id, "이미비활성화된alias")
        await admin_client.delete(f"/entities/{entity_id}/aliases/{alias_id}")

        resp = await admin_client.delete(f"/entities/{entity_id}/aliases/{alias_id}")
        assert resp.status_code == 404

    async def test_deactivate_requires_auth(
        self, client: AsyncClient, admin_client: AsyncClient, entity_id: str
    ):
        alias_id = await _add_alias(admin_client, entity_id, "미인증테스트alias")
        resp = await client.delete(f"/entities/{entity_id}/aliases/{alias_id}")
        assert resp.status_code == 401
