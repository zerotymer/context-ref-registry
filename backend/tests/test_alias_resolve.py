import pytest
from httpx import AsyncClient


@pytest.fixture
async def entity_a(admin_client: AsyncClient) -> str:
    resp = await admin_client.post(
        "/entities",
        json={"type": "FEATURE", "canonical_name": "관리자 사용자 검색"},
    )
    assert resp.status_code == 201
    return resp.json()["data"]["id"]


@pytest.fixture
async def entity_b(admin_client: AsyncClient) -> str:
    resp = await admin_client.post(
        "/entities",
        json={"type": "FEATURE", "canonical_name": "고객 사용자 검색"},
    )
    assert resp.status_code == 201
    return resp.json()["data"]["id"]


async def _add_alias(admin_client: AsyncClient, entity_id: str, alias: str, locale: str = "ko") -> None:
    resp = await admin_client.post(
        f"/entities/{entity_id}/aliases",
        json={"locale": locale, "alias": alias},
    )
    assert resp.status_code == 201


class TestResolveAlias:
    async def test_not_found(self, client: AsyncClient):
        resp = await client.get("/resolve", params={"alias": "없는alias"})
        assert resp.status_code == 200
        data = resp.json()["data"]
        assert data["result"] == "not_found"
        assert data["entity"] is None
        assert data["candidates"] is None

    async def test_resolved_single_match(self, admin_client: AsyncClient, entity_a: str):
        await _add_alias(admin_client, entity_a, "사용자 검색 기능")

        resp = await admin_client.get("/resolve", params={"alias": "사용자 검색 기능"})
        assert resp.status_code == 200
        data = resp.json()["data"]
        assert data["result"] == "resolved"
        assert data["entity"]["id"] == entity_a
        assert data["candidates"] is None

    async def test_ambiguous_multiple_matches(self, admin_client: AsyncClient, entity_a: str, entity_b: str):
        await _add_alias(admin_client, entity_a, "사용자 검색")
        await _add_alias(admin_client, entity_b, "사용자 검색")

        resp = await admin_client.get("/resolve", params={"alias": "사용자 검색"})
        assert resp.status_code == 200
        data = resp.json()["data"]
        assert data["result"] == "ambiguous"
        assert data["entity"] is None
        ids = {c["id"] for c in data["candidates"]}
        assert ids == {entity_a, entity_b}

    async def test_resolve_filtered_by_locale(self, admin_client: AsyncClient, entity_a: str, entity_b: str):
        await _add_alias(admin_client, entity_a, "user search", locale="en")
        await _add_alias(admin_client, entity_b, "user search", locale="ko")

        resp = await admin_client.get("/resolve", params={"alias": "user search", "locale": "en"})
        assert resp.status_code == 200
        data = resp.json()["data"]
        assert data["result"] == "resolved"
        assert data["entity"]["id"] == entity_a

    async def test_resolve_filtered_by_type(self, admin_client: AsyncClient, entity_a: str):
        ui_resp = await admin_client.post(
            "/entities",
            json={"type": "UI_AREA", "canonical_name": "검색 영역"},
        )
        ui_id = ui_resp.json()["data"]["id"]
        await _add_alias(admin_client, entity_a, "공통alias")
        await _add_alias(admin_client, ui_id, "공통alias")

        resp = await admin_client.get("/resolve", params={"alias": "공통alias", "type": "FEATURE"})
        assert resp.status_code == 200
        data = resp.json()["data"]
        assert data["result"] == "resolved"
        assert data["entity"]["id"] == entity_a


class TestAliasEndpoints:
    async def test_add_alias(self, admin_client: AsyncClient, entity_a: str):
        resp = await admin_client.post(
            f"/entities/{entity_a}/aliases",
            json={"locale": "ko", "alias": "테스트alias", "is_primary": True},
        )
        assert resp.status_code == 201
        body = resp.json()
        assert body["ok"] is True
        assert body["data"]["alias"] == "테스트alias"
        assert body["data"]["entity_id"] == entity_a

    async def test_add_alias_entity_not_found(self, admin_client: AsyncClient):
        fake_id = "00000000-0000-0000-0000-000000000000"
        resp = await admin_client.post(
            f"/entities/{fake_id}/aliases",
            json={"locale": "ko", "alias": "어딘가"},
        )
        assert resp.status_code == 404
        assert resp.json()["error"]["code"] == "ENTITY_NOT_FOUND"

    async def test_list_aliases(self, admin_client: AsyncClient, entity_a: str):
        await _add_alias(admin_client, entity_a, "첫번째alias")
        await _add_alias(admin_client, entity_a, "두번째alias")

        resp = await admin_client.get(f"/entities/{entity_a}/aliases")
        assert resp.status_code == 200
        data = resp.json()["data"]
        assert len(data) == 2
        aliases = {a["alias"] for a in data}
        assert aliases == {"첫번째alias", "두번째alias"}

    async def test_list_aliases_entity_not_found(self, client: AsyncClient):
        fake_id = "00000000-0000-0000-0000-000000000000"
        resp = await client.get(f"/entities/{fake_id}/aliases")
        assert resp.status_code == 404
