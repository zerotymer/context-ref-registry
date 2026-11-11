from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import OptionalActorDep, WriterDep
from app.service.audit_service import actor_identifier
from app.auth.policy import check_can_mutate_entity, check_can_view_entity, visible_project_ids
from app.db.session import get_session
from app.domain.enums import ContextType, Locale
from app.domain.schemas import ContextCreate, ContextRead, OkResponse
from app.service.context_service import ContextService
from app.service.entity_service import EntityService

router = APIRouter(tags=["contexts"])

SessionDep = Annotated[AsyncSession, Depends(get_session)]


@router.post("/entities/{entity_ref}/contexts", status_code=201, response_model=OkResponse[ContextRead])
async def add_context(
    entity_ref: str,
    body: ContextCreate,
    session: SessionDep,
    actor: WriterDep,
) -> OkResponse[ContextRead]:
    entity = await EntityService(session).resolve_ref(entity_ref)
    check_can_mutate_entity(entity.project_id, actor)
    ctx = await ContextService(session).add_context(entity.id, body, actor=actor_identifier(actor))
    return OkResponse(data=ContextRead.model_validate(ctx))


@router.get("/entities/{entity_ref}/contexts", response_model=OkResponse[list[ContextRead]])
async def list_contexts(
    entity_ref: str,
    session: SessionDep,
    actor: OptionalActorDep,
    context_type: ContextType | None = Query(None, description="Filter by context type"),
    language: Locale | None = Query(None, description="Filter by language"),
) -> OkResponse[list[ContextRead]]:
    entity = await EntityService(session).resolve_ref(entity_ref)
    check_can_view_entity(entity.project_id, actor)
    contexts = await ContextService(session).list_contexts(entity.id, context_type, language)
    return OkResponse(data=[ContextRead.model_validate(c) for c in contexts])
