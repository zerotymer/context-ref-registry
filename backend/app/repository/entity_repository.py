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
