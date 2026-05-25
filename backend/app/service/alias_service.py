from __future__ import annotations

import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.enums import EntityType, Locale
from app.domain.models import EntityAlias
from app.domain.schemas import AliasCreate, EntityRead, ResolveResult
from app.exceptions import RegistryError
from app.repository.alias_repository import AliasRepository
from app.repository.entity_repository import EntityRepository


class AliasService:
    def __init__(self, session: AsyncSession) -> None:
        self._alias_repo = AliasRepository(session)
        self._entity_repo = EntityRepository(session)

    async def add_alias(self, entity_id: uuid.UUID, data: AliasCreate) -> EntityAlias:
        entity = await self._entity_repo.get_by_id(entity_id)
        if entity is None:
            raise RegistryError(
                code="ENTITY_NOT_FOUND",
                message=f"Entity {entity_id} not found",
                status_code=404,
            )
        return await self._alias_repo.add(entity_id, data)

    async def list_aliases(self, entity_id: uuid.UUID) -> list[EntityAlias]:
        entity = await self._entity_repo.get_by_id(entity_id)
        if entity is None:
            raise RegistryError(
                code="ENTITY_NOT_FOUND",
                message=f"Entity {entity_id} not found",
                status_code=404,
            )
        return await self._alias_repo.list_by_entity(entity_id)

    async def resolve(
        self,
        alias: str,
        locale: Locale | None = None,
        entity_type: EntityType | None = None,
    ) -> ResolveResult:
        entities = await self._alias_repo.resolve(alias, locale, entity_type)

        if not entities:
            return ResolveResult(result="not_found")

        if len(entities) == 1:
            return ResolveResult(
                result="resolved",
                entity=EntityRead.model_validate(entities[0]),
            )

        return ResolveResult(
            result="ambiguous",
            candidates=[EntityRead.model_validate(e) for e in entities],
        )
