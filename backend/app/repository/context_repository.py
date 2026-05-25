from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.enums import ContextType, Locale
from app.domain.models import EntityContext
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
