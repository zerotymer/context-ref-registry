from __future__ import annotations

import logging

from app.config import settings

logger = logging.getLogger(__name__)


class EmbeddingService:
    """Generates vector embeddings via OpenAI API.

    Returns None silently when OPENAI_API_KEY is not configured so the
    application degrades gracefully to keyword-only search.
    """

    def __init__(self) -> None:
        self._client = None
        if settings.openai_api_key:
            from openai import AsyncOpenAI
            self._client = AsyncOpenAI(api_key=settings.openai_api_key)

    @property
    def enabled(self) -> bool:
        return self._client is not None

    async def embed(self, text: str) -> list[float] | None:
        if not self._client:
            return None
        try:
            response = await self._client.embeddings.create(
                model=settings.embedding_model,
                input=text,
            )
            return response.data[0].embedding
        except Exception:
            logger.exception("Failed to generate embedding")
            return None


_svc: EmbeddingService | None = None


def get_embedding_service() -> EmbeddingService:
    global _svc
    if _svc is None:
        _svc = EmbeddingService()
    return _svc
