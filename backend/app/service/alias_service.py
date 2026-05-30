from __future__ import annotations

import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.enums import EntityType, Locale
from app.domain.models import EntityAlias
from app.domain.schemas import AliasCreate, EntityRead, ResolveResult
from app.exceptions import RegistryError
from app.repository.alias_repository import AliasRepository
from app.repository.entity_repository import EntityRepository
from app.service.audit_service import AuditService


class AliasService:
    def __init__(self, session: AsyncSession) -> None:
        self._alias_repo = AliasRepository(session)
        self._entity_repo = EntityRepository(session)
        self._audit = AuditService(session)

    async def add_alias(
        self, entity_id: uuid.UUID, data: AliasCreate, actor: str | None = None
    ) -> EntityAlias:
        entity = await self._entity_repo.get_by_id(entity_id)
        if entity is None:
            raise RegistryError(
                code="ENTITY_NOT_FOUND",
                message=f"Entity {entity_id} not found",
                status_code=404,
            )
        alias = await self._alias_repo.add(entity_id, data)
        await self._audit.log(
            actor=actor or "system",
            action="alias_add",
            target_type="alias",
            target_id=str(alias.id),
            after_snapshot={
                "id": str(alias.id),
                "entity_id": str(alias.entity_id),
                "locale": alias.locale,
                "alias": alias.alias,
                "is_primary": alias.is_primary,
            },
        )
        return alias

    async def deactivate_alias(
        self, entity_id: uuid.UUID, alias_id: uuid.UUID, actor: str | None = None
    ) -> EntityAlias:
        alias = await self._alias_repo.deactivate(entity_id, alias_id)
        if alias is None:
            raise RegistryError(
                code="ALIAS_NOT_FOUND",
                message=f"Active alias {alias_id} not found for entity {entity_id}",
                status_code=404,
            )
        await self._audit.log(
            actor=actor or "system",
            action="alias_deactivate",
            target_type="alias",
            target_id=str(alias.id),
            after_snapshot={"id": str(alias.id), "is_active": False},
        )
        return alias

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
        visible_project_ids: list[str] | None = None,
    ) -> ResolveResult:
        entities = await self._alias_repo.resolve(alias, locale, entity_type, visible_project_ids=visible_project_ids)

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
