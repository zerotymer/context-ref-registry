"""pgvector semantic search tests.

Vector search is only exercised when OPENAI_API_KEY is configured.
Tests here verify that:
  - keyword search still works normally (no regression)
  - when embedding service is disabled, vector path is a no-op
  - search_by_vector repository method executes without error when pgvector is available
"""
import os

import pytest
from httpx import AsyncClient
from sqlalchemy import text

from app.service.embedding_service import EmbeddingService


async def _create(admin_client: AsyncClient, entity_type: str, name: str) -> dict:
    r = await admin_client.post("/entities", json={"type": entity_type, "canonical_name": name})
    assert r.status_code == 201
    return r.json()["data"]


async def _add_context(admin_client: AsyncClient, entity_id: str, body: str) -> dict:
    r = await admin_client.post(
        f"/entities/{entity_id}/contexts",
        json={"context_type": "summary", "body": body, "language": "ko"},
    )
    assert r.status_code == 201
    return r.json()["data"]


class TestEmbeddingServiceDisabled:
    """When OPENAI_API_KEY is absent, embedding service must be a no-op."""

    def test_not_enabled_without_api_key(self):
        svc = EmbeddingService.__new__(EmbeddingService)
        svc._client = None
        assert svc.enabled is False

    async def test_embed_returns_none_when_disabled(self):
        svc = EmbeddingService.__new__(EmbeddingService)
        svc._client = None
        result = await svc.embed("hello")
        assert result is None


class TestSearchWithoutEmbedding:
    """GET /search falls back to keyword search when embedding is disabled."""

    async def test_alias_exact_still_works(self, admin_client: AsyncClient):
        entity = await _create(admin_client, "FEATURE", "벡터 테스트 기능")
        r = await admin_client.post(
            f"/entities/{entity['id']}/aliases",
            json={"locale": "ko", "alias": "벡터alias"},
        )
        assert r.status_code == 201

        resp = await admin_client.get("/search", params={"q": "벡터alias"})
        assert resp.status_code == 200
        data = resp.json()["data"]
        assert any(e["id"] == entity["id"] and e["match_reason"] == "alias_exact" for e in data)

    async def test_canonical_partial_still_works(self, admin_client: AsyncClient):
        entity = await _create(admin_client, "UI_AREA", "벡터 전용 화면 영역")

        resp = await admin_client.get("/search", params={"q": "전용 화면"})
        assert resp.status_code == 200
        ids = [e["id"] for e in resp.json()["data"]]
        assert entity["id"] in ids

    async def test_vector_fallback_is_noop_without_key(self, admin_client: AsyncClient):
        """No extra results appear from vector search when embedding is disabled."""
        entity = await _create(admin_client, "FEATURE", "완전히 새로운 기능명zyx")
        await _add_context(admin_client, entity["id"], "이 entity는 검색에 등장하면 안 됩니다")

        # Query that won't match keyword search
        resp = await admin_client.get("/search", params={"q": "never_match_keyword_xqz"})
        assert resp.status_code == 200
        ids = [e["id"] for e in resp.json()["data"]]
        # With no embedding service, vector fallback is skipped → entity NOT found
        assert entity["id"] not in ids


class TestVectorSearchRepository:
    """Repository-level vector search test — requires pgvector in the test DB."""

    async def test_search_by_vector_skipped_without_pgvector(self, admin_client: AsyncClient):
        """search_by_vector gracefully returns empty list if no embeddings exist."""
        from app.db.session import async_session_factory
        from app.repository.entity_repository import EntityRepository

        dummy_embedding = [0.0] * 1536

        async with async_session_factory() as session:
            # Check if pgvector is available
            try:
                await session.execute(text("SELECT 1 FROM context_embedding LIMIT 0"))
            except Exception:
                pytest.skip("pgvector not available in this test environment")

            repo = EntityRepository(session)
            results = await repo.search_by_vector(dummy_embedding, limit=5)
        # Should return empty list when no embeddings stored
        assert results == []
