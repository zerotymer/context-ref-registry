from __future__ import annotations

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import OptionalActorDep, WriterDep
from app.service.audit_service import actor_identifier
from app.auth.policy import check_can_mutate_entity, check_can_view_entity, visible_project_ids
from app.db.session import get_session
from app.domain.enums import EntityType, Locale
from app.domain.schemas import AliasCreate, AliasRead, OkResponse, ResolveResult
from app.service.alias_service import AliasService
from app.service.entity_service import EntityService

router = APIRouter(tags=["aliases"])

SessionDep = Annotated[AsyncSession, Depends(get_session)]


@router.post("/entities/{entity_ref}/aliases", status_code=201, response_model=OkResponse[AliasRead])
async def add_alias(
    entity_ref: str,
    body: AliasCreate,
    session: SessionDep,
    actor: WriterDep,
) -> OkResponse[AliasRead]:
    entity = await EntityService(session).resolve_ref(entity_ref)
    check_can_mutate_entity(entity.project_id, actor)
    alias = await AliasService(session).add_alias(entity.id, body, actor=actor_identifier(actor))
    return OkResponse(data=AliasRead.model_validate(alias))


@router.delete(
    "/entities/{entity_ref}/aliases/{alias_id}",
    status_code=200,
    response_model=OkResponse[AliasRead],
)
async def deactivate_alias(
    entity_ref: str,
    alias_id: uuid.UUID,
    session: SessionDep,
    actor: WriterDep,
) -> OkResponse[AliasRead]:
    entity = await EntityService(session).resolve_ref(entity_ref)
    check_can_mutate_entity(entity.project_id, actor)
    alias = await AliasService(session).deactivate_alias(entity.id, alias_id, actor=actor_identifier(actor))
    return OkResponse(data=AliasRead.model_validate(alias))


@router.get("/entities/{entity_ref}/aliases", response_model=OkResponse[list[AliasRead]])
async def list_aliases(
    entity_ref: str,
    session: SessionDep,
    actor: OptionalActorDep,
) -> OkResponse[list[AliasRead]]:
    entity = await EntityService(session).resolve_ref(entity_ref)
    check_can_view_entity(entity.project_id, actor)
    aliases = await AliasService(session).list_aliases(entity.id)
    return OkResponse(data=[AliasRead.model_validate(a) for a in aliases])


@router.get("/resolve", response_model=OkResponse[ResolveResult])
async def resolve_alias(
    session: SessionDep,
    actor: OptionalActorDep,
    alias: str = Query(..., description="Alias string to resolve"),
    locale: Locale | None = Query(None, description="Filter by locale"),
    type: EntityType | None = Query(None, description="Filter by entity type"),
) -> OkResponse[ResolveResult]:
    result = await AliasService(session).resolve(alias, locale, type, visible_project_ids=visible_project_ids(actor))
    return OkResponse(data=result)
