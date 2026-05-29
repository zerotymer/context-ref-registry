"""GET /search endpoint tests."""
import pytest
from httpx import AsyncClient


async def _create(admin_client: AsyncClient, entity_type: str, name: str) -> dict:
    r = await admin_client.post("/entities", json={"type": entity_type, "canonical_name": name})
    assert r.status_code == 201
    return r.json()["data"]


async def _add_alias(admin_client: AsyncClient, entity_id: str, alias: str, locale: str = "ko") -> None:
    r = await admin_client.post(f"/entities/{entity_id}/aliases", json={"locale": locale, "alias": alias})
    assert r.status_code == 201


class TestSearchAPI:
    async def test_alias_exact_match(self, admin_client: AsyncClient):
        entity = await _create(admin_client, "FEATURE", "기능 X")
        await _add_alias(admin_client, entity["id"], "정확한alias")

        r = await admin_client.get("/search", params={"q": "정확한alias"})
        assert r.status_code == 200
        results = r.json()["data"]
        ids = [e["id"] for e in results]
        assert entity["id"] in ids
        match = next(e for e in results if e["id"] == entity["id"])
        assert match["match_reason"] == "alias_exact"

    async def test_canonical_name_partial_match(self, admin_client: AsyncClient):
        entity = await _create(admin_client, "UI_AREA", "사용자 목록 화면")

        r = await admin_client.get("/search", params={"q": "목록 화면"})
        assert r.status_code == 200
        ids = [e["id"] for e in r.json()["data"]]
        assert entity["id"] in ids

    async def test_type_filter(self, admin_client: AsyncClient):
        feat = await _create(admin_client, "FEATURE", "공통 기능")
        area = await _create(admin_client, "UI_AREA", "공통 영역")

        r = await admin_client.get("/search", params={"q": "공통", "types": "FEATURE"})
        assert r.status_code == 200
        ids = [e["id"] for e in r.json()["data"]]
        assert feat["id"] in ids
        assert area["id"] not in ids

    async def test_no_results(self, client: AsyncClient):
        r = await client.get("/search", params={"q": "존재하지않는쿼리xyz"})
        assert r.status_code == 200
        assert r.json()["data"] == []

    async def test_empty_query_returns_422(self, client: AsyncClient):
        r = await client.get("/search", params={"q": ""})
        assert r.status_code == 422
