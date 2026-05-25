from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.enums import EntityType, Locale
from app.domain.models import Entity, EntityAlias
from app.domain.schemas import AliasCreate


class AliasRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def add(self, entity_id: uuid.UUID, data: AliasCreate) -> EntityAlias:
        alias = EntityAlias(
            entity_id=entity_id,
            locale=data.locale,
            alias=data.alias,
            is_primary=data.is_primary,
        )
        self._session.add(alias)
        await self._session.flush()
        await self._session.refresh(alias)
        return alias

    async def list_by_entity(self, entity_id: uuid.UUID) -> list[EntityAlias]:
        result = await self._session.execute(
            select(EntityAlias)
            .where(EntityAlias.entity_id == entity_id, EntityAlias.is_active == True)  # noqa: E712
            .order_by(EntityAlias.created_at)
        )
        return list(result.scalars().all())

    async def resolve(
        self,
        alias: str,
        locale: Locale | None = None,
        entity_type: EntityType | None = None,
    ) -> list[Entity]:
        stmt = (
            select(Entity)
            .join(EntityAlias, EntityAlias.entity_id == Entity.id)
            .where(EntityAlias.alias == alias, EntityAlias.is_active == True)  # noqa: E712
        )
        if locale is not None:
            stmt = stmt.where(EntityAlias.locale == locale)
        if entity_type is not None:
            stmt = stmt.where(Entity.type == entity_type)

        result = await self._session.execute(stmt.distinct())
        return list(result.scalars().all())
