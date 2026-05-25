from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.models import Entity
from app.domain.schemas import EntityCreate, EntityUpdate


class EntityRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(self, data: EntityCreate) -> Entity:
        entity = Entity(
            id=data.id if data.id is not None else uuid.uuid4(),
            type=data.type,
            canonical_name=data.canonical_name,
            description=data.description,
            status=data.status,
            confidence=data.confidence,
        )
        self._session.add(entity)
        await self._session.flush()
        await self._session.refresh(entity)
        return entity

    async def get_by_id(self, entity_id: uuid.UUID) -> Entity | None:
        result = await self._session.execute(
            select(Entity).where(Entity.id == entity_id)
        )
        return result.scalar_one_or_none()

    async def update(self, entity: Entity, data: EntityUpdate) -> Entity:
        for field, value in data.model_dump(exclude_unset=True).items():
            setattr(entity, field, value)
        await self._session.flush()
        await self._session.refresh(entity)
        return entity

    async def search(
        self,
        query: str,
        types: list | None = None,
        limit: int = 10,
    ) -> list[tuple[Entity, str]]:
        from app.domain.models import EntityAlias

        results: list[tuple[Entity, str]] = []
        seen_ids: set[uuid.UUID] = set()

        # 1. alias exact match
        stmt = (
            select(Entity)
            .join(EntityAlias, EntityAlias.entity_id == Entity.id)
            .where(EntityAlias.alias == query, EntityAlias.is_active == True)  # noqa: E712
        )
        if types:
            stmt = stmt.where(Entity.type.in_(types))
        result = await self._session.execute(stmt.distinct().limit(limit))
        for entity in result.scalars().all():
            if entity.id not in seen_ids:
                seen_ids.add(entity.id)
                results.append((entity, "alias_exact"))

        # 2. canonical_name partial match (ILIKE)
        remaining = limit - len(results)
        if remaining > 0:
            stmt2 = select(Entity).where(Entity.canonical_name.ilike(f"%{query}%"))
            if types:
                stmt2 = stmt2.where(Entity.type.in_(types))
            result2 = await self._session.execute(stmt2.limit(remaining))
            for entity in result2.scalars().all():
                if entity.id not in seen_ids:
                    seen_ids.add(entity.id)
                    results.append((entity, "canonical_name_partial"))

        return results
