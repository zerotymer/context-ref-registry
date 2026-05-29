from __future__ import annotations

import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.enums import ContextType, Locale
from app.domain.models import EntityContext
from app.domain.schemas import ContextCreate
from app.exceptions import RegistryError
from app.repository.context_repository import ContextRepository
from app.repository.entity_repository import EntityRepository
from app.service.audit_service import AuditService


class ContextService:
    def __init__(self, session: AsyncSession) -> None:
        self._context_repo = ContextRepository(session)
        self._entity_repo = EntityRepository(session)
        self._audit = AuditService(session)

    async def add_context(
        self, entity_id: uuid.UUID, data: ContextCreate, actor: str | None = None
    ) -> EntityContext:
        entity = await self._entity_repo.get_by_id(entity_id)
        if entity is None:
            raise RegistryError(
                code="ENTITY_NOT_FOUND",
                message=f"Entity {entity_id} not found",
                status_code=404,
            )
        ctx = await self._context_repo.add(entity_id, data)
        await self._audit.log(
            actor=actor or "system",
            action="context_add",
            target_type="context",
            target_id=str(ctx.id),
            after_snapshot={
                "id": str(ctx.id),
                "entity_id": str(ctx.entity_id),
                "context_type": ctx.context_type if isinstance(ctx.context_type, str) else ctx.context_type.value,
                "title": ctx.title,
                "language": ctx.language if isinstance(ctx.language, str) else ctx.language.value,
            },
        )
        return ctx

    async def list_contexts(
        self,
        entity_id: uuid.UUID,
        context_type: ContextType | None = None,
        language: Locale | None = None,
    ) -> list[EntityContext]:
        entity = await self._entity_repo.get_by_id(entity_id)
        if entity is None:
            raise RegistryError(
                code="ENTITY_NOT_FOUND",
                message=f"Entity {entity_id} not found",
                status_code=404,
            )
        return await self._context_repo.list_by_entity(entity_id, context_type, language)
