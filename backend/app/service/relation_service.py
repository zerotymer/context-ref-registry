from __future__ import annotations

import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.enums import RelationType
from app.domain.models import EntityRelation
from app.domain.schemas import RelationCreate
from app.exceptions import RegistryError
from app.repository.entity_repository import EntityRepository
from app.repository.relation_repository import RelationRepository


class RelationService:
    def __init__(self, session: AsyncSession) -> None:
        self._relation_repo = RelationRepository(session)
        self._entity_repo = EntityRepository(session)

    async def create_relation(self, data: RelationCreate) -> EntityRelation:
        from_entity = await self._entity_repo.get_by_id(data.from_entity_id)
        if from_entity is None:
            raise RegistryError(
                code="ENTITY_NOT_FOUND",
                message=f"Entity {data.from_entity_id} not found",
                status_code=404,
            )
        to_entity = await self._entity_repo.get_by_id(data.to_entity_id)
        if to_entity is None:
            raise RegistryError(
                code="ENTITY_NOT_FOUND",
                message=f"Entity {data.to_entity_id} not found",
                status_code=404,
            )
        return await self._relation_repo.add(data)

    async def list_relations(
        self,
        entity_id: uuid.UUID,
        direction: str = "both",
        relation_type: RelationType | None = None,
        max_depth: int = 1,
    ) -> list[EntityRelation]:
        entity = await self._entity_repo.get_by_id(entity_id)
        if entity is None:
            raise RegistryError(
                code="ENTITY_NOT_FOUND",
                message=f"Entity {entity_id} not found",
                status_code=404,
            )
        return await self._relation_repo.list_by_entity(entity_id, direction, relation_type, max_depth)
