from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.enums import ContextType, Locale
from app.domain.models import ContextEmbedding, EntityContext
from app.domain.schemas import ContextCreate


class ContextRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def add(self, entity_id: uuid.UUID, data: ContextCreate) -> EntityContext:
        ctx = EntityContext(
            entity_id=entity_id,
            context_type=data.context_type,
            title=data.title,
            body=data.body,
            language=data.language,
            source_ref_id=data.source_ref_id,
        )
        self._session.add(ctx)
        await self._session.flush()
        await self._session.refresh(ctx)
        return ctx

    async def get_by_id(self, context_id: uuid.UUID) -> EntityContext | None:
        result = await self._session.execute(
            select(EntityContext).where(EntityContext.id == context_id)
        )
        return result.scalar_one_or_none()

    async def upsert_embedding(self, context_id: uuid.UUID, embedding: list[float], model: str) -> None:
        existing = await self._session.get(ContextEmbedding, context_id)
        if existing is not None:
            existing.embedding = embedding
            existing.embedding_model = model
        else:
            self._session.add(ContextEmbedding(context_id=context_id, embedding=embedding, embedding_model=model))
        await self._session.flush()

    async def list_by_entity(
        self,
        entity_id: uuid.UUID,
        context_type: ContextType | None = None,
        language: Locale | None = None,
    ) -> list[EntityContext]:
        stmt = (
            select(EntityContext)
            .where(EntityContext.entity_id == entity_id)
            .order_by(EntityContext.created_at)
        )
        if context_type is not None:
            stmt = stmt.where(EntityContext.context_type == context_type)
        if language is not None:
            stmt = stmt.where(EntityContext.language == language)

        result = await self._session.execute(stmt)
        return list(result.scalars().all())
