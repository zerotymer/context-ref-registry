from __future__ import annotations

import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.enums import EntityStatus, EntityType
from app.domain.models import Entity
from app.domain.schemas import EntityCreate, EntityUpdate
from app.exceptions import RegistryError
from app.repository.entity_repository import EntityRepository


class EntityService:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._repo = EntityRepository(session)

    async def list(
        self,
        status: EntityStatus | None,
        types: list[EntityType] | None,
        tags: list[str] | None,
        limit: int,
        offset: int,
        sort: str,
        order: str,
    ) -> tuple[list[Entity], int]:
        return await self._repo.list(status, types, tags, limit, offset, sort, order)

    async def create(self, data: EntityCreate) -> Entity:
        entity = await self._repo.create(data)
        if data.tags:
            await self._repo.replace_tags(entity.id, data.tags)
            await self._session.refresh(entity)
        return entity

    async def get_by_id(self, entity_id: uuid.UUID) -> Entity:
        entity = await self._repo.get_by_id(entity_id)
        if entity is None:
            raise RegistryError(
                code="ENTITY_NOT_FOUND",
                message=f"Entity {entity_id} not found",
                status_code=404,
            )
        return entity

    async def update(self, entity_id: uuid.UUID, data: EntityUpdate) -> Entity:
        entity = await self.get_by_id(entity_id)
        entity_fields = {k: v for k, v in data.model_dump(exclude_unset=True).items() if k != "tags"}
        if entity_fields:
            await self._repo.update(entity, EntityUpdate(**entity_fields))
        if data.tags is not None:
            await self._repo.replace_tags(entity_id, data.tags)
            await self._session.refresh(entity)
        return entity

    async def add_tag(self, entity_id: uuid.UUID, tag: str) -> Entity:
        entity = await self.get_by_id(entity_id)
        await self._repo.add_tag(entity_id, tag)
        await self._session.refresh(entity)
        return entity

    async def remove_tag(self, entity_id: uuid.UUID, tag: str) -> None:
        await self.get_by_id(entity_id)
        await self._repo.remove_tag(entity_id, tag)

    async def list_all_tags(self) -> list[tuple[str, int]]:
        return await self._repo.list_all_tags()
