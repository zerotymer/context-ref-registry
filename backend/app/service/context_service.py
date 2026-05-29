from __future__ import annotations

import asyncio
import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.domain.enums import ContextType, Locale
from app.domain.models import EntityContext
from app.domain.schemas import ContextCreate
from app.exceptions import RegistryError
from app.repository.context_repository import ContextRepository
from app.repository.entity_repository import EntityRepository
from app.service.audit_service import AuditService
from app.service.embedding_service import get_embedding_service


class ContextService:
    def __init__(self, session: AsyncSession) -> None:
        self._context_repo = ContextRepository(session)
        self._entity_repo = EntityRepository(session)
        self._audit = AuditService(session)
        self._session = session

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

        emb_svc = get_embedding_service()
        if emb_svc.enabled:
            context_id = ctx.id
            body = ctx.body
            asyncio.ensure_future(self._generate_embedding(context_id, body))

        return ctx

    async def _generate_embedding(self, context_id: uuid.UUID, body: str) -> None:
        from app.db.session import async_session_factory

        emb_svc = get_embedding_service()
        embedding = await emb_svc.embed(body)
        if embedding is None:
            return
        async with async_session_factory() as session:
            ctx_repo = ContextRepository(session)
            await ctx_repo.upsert_embedding(context_id, embedding, settings.embedding_model)
            await session.commit()

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
