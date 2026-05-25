"""Integration tests using docs/10 example data.

Validates the 6 DoD criteria from docs/11-codex-task-brief.md using
the shared fixtures defined in conftest.py.
"""
import pytest
from httpx import AsyncClient


class TestDocsExamplesIntegration:
    """End-to-end scenarios mirroring docs/10 example data."""

    async def test_entity_uuid_lookup(
        self,
        client: AsyncClient,
        entity_user_search_feature: dict,
    ):
        """DoD 1: entity 생성 후 UUID로 조회된다."""
        resp = await client.get(f"/entities/{entity_user_search_feature['id']}")
        assert resp.status_code == 200
        data = resp.json()["data"]
        assert data["id"] == entity_user_search_feature["id"]
        assert data["type"] == "FEATURE"
        assert data["canonical_name"] == "사용자 검색"

    async def test_alias_ambiguous(
        self,
        client: AsyncClient,
        entity_user_search_area: dict,
        entity_user_search_feature: dict,
    ):
        """DoD 2: alias가 중복되면 ambiguous를 반환한다 (docs/10 example 3).

        '사용자 검색' alias is shared by both area (ko: '회원 검색 조건' etc.)
        and feature (ko: '사용자 검색').  We explicitly add the same alias to
        both entities here to guarantee the collision.
        """
        shared_alias = "공통검색alias"
        for eid in [entity_user_search_area["id"], entity_user_search_feature["id"]]:
            r = await client.post(
                f"/entities/{eid}/aliases",
                json={"locale": "ko", "alias": shared_alias},
            )
            assert r.status_code == 201

        resp = await client.get("/resolve", params={"alias": shared_alias, "locale": "ko"})
        assert resp.status_code == 200
        data = resp.json()["data"]
        assert data["result"] == "ambiguous"
        ids = {c["id"] for c in data["candidates"]}
        assert entity_user_search_area["id"] in ids
        assert entity_user_search_feature["id"] in ids

    async def test_alias_resolved(
        self,
        client: AsyncClient,
        entity_user_db: dict,
    ):
        """DoD 3: alias가 하나만 매칭되면 resolved를 반환한다."""
        resp = await client.get("/resolve", params={"alias": "사용자 DB", "locale": "ko"})
        assert resp.status_code == 200
        data = resp.json()["data"]
        assert data["result"] == "resolved"
        assert data["entity"]["id"] == entity_user_db["id"]

    async def test_alias_not_found(self, client: AsyncClient):
        """DoD 4: 존재하지 않는 alias는 not_found를 반환한다."""
        resp = await client.get("/resolve", params={"alias": "존재하지않는alias_xyz"})
        assert resp.status_code == 200
        assert resp.json()["data"]["result"] == "not_found"

    async def test_context_bundle_includes_root_and_related(
        self,
        client: AsyncClient,
        entity_user_search_feature: dict,
        relation_area_to_feature: dict,
        relation_feature_to_db: dict,
    ):
        """DoD 5: context bundle은 root entity와 직접 relation entity를 포함한다."""
        resp = await client.post("/context-bundle", json={
            "root_ids": [entity_user_search_feature["id"]],
            "include_relations": ["RELATED_TO", "READS_FROM"],
            "include_types": ["UI_AREA", "FEATURE", "INFRA_UNIT"],
            "max_depth": 1,
            "token_budget": 4000,
        })
        assert resp.status_code == 200
        data = resp.json()["data"]
        all_ids = {e["id"] for e in data["roots"]} | {e["id"] for e in data["entities"]}
        assert entity_user_search_feature["id"] in all_ids
        # READS_FROM direction: feature → infra_unit
        assert "ed832d61-3319-4d61-83d4-6a29f68932a5" in all_ids

    async def test_context_bundle_max_depth(
        self,
        client: AsyncClient,
        entity_user_search_area: dict,
        entity_user_search_feature: dict,
        entity_user_db: dict,
        relation_area_to_feature: dict,
        relation_feature_to_db: dict,
    ):
        """DoD 6: max_depth가 relation 탐색에 적용된다.

        area --RELATED_TO--> feature --READS_FROM--> db
        max_depth=1 from area: only area+feature visible, db excluded.
        """
        resp = await client.post("/context-bundle", json={
            "root_ids": [entity_user_search_area["id"]],
            "max_depth": 1,
            "token_budget": 4000,
        })
        assert resp.status_code == 200
        data = resp.json()["data"]
        all_ids = {e["id"] for e in data["roots"]} | {e["id"] for e in data["entities"]}
        assert entity_user_search_area["id"] in all_ids
        assert entity_user_search_feature["id"] in all_ids
        assert entity_user_db["id"] not in all_ids

    async def test_context_bundle_deprecated_warning(self, client: AsyncClient):
        """DoD 7: deprecated entity가 bundle에 포함되면 warning이 반환된다."""
        old = (await client.post("/entities", json={"type": "FEATURE", "canonical_name": "구 기능"})).json()["data"]
        new = (await client.post("/entities", json={"type": "FEATURE", "canonical_name": "신 기능"})).json()["data"]
        await client.patch(f"/entities/{old['id']}", json={
            "status": "deprecated",
            "replacement_entity_id": new["id"],
        })

        resp = await client.post("/context-bundle", json={
            "root_ids": [old["id"]],
            "max_depth": 0,
            "token_budget": 4000,
        })
        assert resp.status_code == 200
        data = resp.json()["data"]
        assert len(data["warnings"]) == 1
        w = data["warnings"][0]
        assert w["entity_id"] == old["id"]
        assert w["type"] == "deprecated_entity"
        assert w["replacement_entity_id"] == new["id"]

    async def test_batch_ingest_sample(
        self,
        client: AsyncClient,
    ):
        """DoD batch ingest sample: 정상 배치 → created 건수 반환."""
        payload = {
            "source": {"type": "screen_spec", "name": "sample.md", "uri": "file://sample.md", "version": "2026-05-25"},
            "entities": [
                {
                    "id": "0d18b76a-6c0e-45b4-9289-6bdfc2e87e5a",
                    "type": "UI_AREA",
                    "canonical_name": "사용자 검색 조건 영역",
                    "status": "active",
                    "confidence": 1.0,
                    "aliases": {"ko": ["검색 조건"], "en": ["Search Criteria"]},
                    "contexts": [{"context_type": "summary", "body": "검색 조건 영역 요약", "language": "ko"}],
                    "metadata": {},
                },
                {
                    "id": "1c9323e9-46a4-4665-b2d1-c37e4f3b19e0",
                    "type": "FEATURE",
                    "canonical_name": "사용자 검색",
                    "status": "active",
                    "confidence": 1.0,
                    "aliases": {"ko": ["사용자 조회"], "en": ["User Search"]},
                    "contexts": [],
                    "metadata": {},
                },
            ],
            "relations": [{
                "from_entity_id": "0d18b76a-6c0e-45b4-9289-6bdfc2e87e5a",
                "to_entity_id": "1c9323e9-46a4-4665-b2d1-c37e4f3b19e0",
                "relation_type": "RELATED_TO",
            }],
        }
        resp = await client.post("/ingest/batch", json=payload)
        assert resp.status_code == 200
        data = resp.json()["data"]
        assert data["created"]["entities"] == 2
        assert data["created"]["relations"] == 1
        assert data["created"]["contexts"] == 1
