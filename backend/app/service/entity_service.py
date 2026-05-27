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
        self._repo = EntityRepository(session)

    async def list(
        self,
        status: EntityStatus | None,
        types: list[EntityType] | None,
        limit: int,
        offset: int,
        sort: str,
        order: str,
    ) -> tuple[list[Entity], int]:
        return await self._repo.list(status, types, limit, offset, sort, order)

    async def create(self, data: EntityCreate) -> Entity:
        return await self._repo.create(data)

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
        return await self._repo.update(entity, data)
