from __future__ import annotations

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import get_current_user, get_optional_user
from app.auth.policy import AccessPolicy
from app.db.session import get_session
from app.domain.enums import EntityType, Locale
from app.domain.models import UserAccount
from app.domain.schemas import AliasCreate, AliasRead, OkResponse, ResolveResult
from app.service.alias_service import AliasService
from app.service.entity_service import EntityService

router = APIRouter(tags=["aliases"])

SessionDep = Annotated[AsyncSession, Depends(get_session)]


@router.post("/entities/{entity_id}/aliases", status_code=201, response_model=OkResponse[AliasRead])
async def add_alias(
    entity_id: uuid.UUID,
    body: AliasCreate,
    session: SessionDep,
    user: Annotated[UserAccount, Depends(get_current_user)],
) -> OkResponse[AliasRead]:
    policy = AccessPolicy(session)
    user_project_ids = await policy.get_user_project_ids(user.id)
    entity = await EntityService(session).get_by_id(entity_id)
    policy.check_can_mutate_entity(entity.project_id, user, user_project_ids)
    alias = await AliasService(session).add_alias(entity_id, body)
    return OkResponse(data=AliasRead.model_validate(alias))


@router.get("/entities/{entity_id}/aliases", response_model=OkResponse[list[AliasRead]])
async def list_aliases(
    entity_id: uuid.UUID,
    session: SessionDep,
    user: Annotated[UserAccount | None, Depends(get_optional_user)],
) -> OkResponse[list[AliasRead]]:
    policy = AccessPolicy(session)
    visible_ids = await policy.get_visible_project_ids(user)
    entity = await EntityService(session).get_by_id(entity_id)
    policy.check_can_view_entity(entity.project_id, user, visible_ids)
    aliases = await AliasService(session).list_aliases(entity_id)
    return OkResponse(data=[AliasRead.model_validate(a) for a in aliases])


@router.get("/resolve", response_model=OkResponse[ResolveResult])
async def resolve_alias(
    session: SessionDep,
    user: Annotated[UserAccount | None, Depends(get_optional_user)],
    alias: str = Query(..., description="Alias string to resolve"),
    locale: Locale | None = Query(None, description="Filter by locale"),
    type: EntityType | None = Query(None, description="Filter by entity type"),
) -> OkResponse[ResolveResult]:
    policy = AccessPolicy(session)
    visible_ids = await policy.get_visible_project_ids(user)
    result = await AliasService(session).resolve(alias, locale, type, visible_project_ids=visible_ids)
    return OkResponse(data=result)
