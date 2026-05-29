from __future__ import annotations

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import get_current_user, get_optional_user
from app.auth.policy import AccessPolicy
from app.db.session import get_session
from app.domain.enums import ContextType, Locale
from app.domain.models import UserAccount
from app.domain.schemas import ContextCreate, ContextRead, OkResponse
from app.service.context_service import ContextService
from app.service.entity_service import EntityService

router = APIRouter(tags=["contexts"])

SessionDep = Annotated[AsyncSession, Depends(get_session)]


@router.post("/entities/{entity_id}/contexts", status_code=201, response_model=OkResponse[ContextRead])
async def add_context(
    entity_id: uuid.UUID,
    body: ContextCreate,
    session: SessionDep,
    user: Annotated[UserAccount, Depends(get_current_user)],
) -> OkResponse[ContextRead]:
    policy = AccessPolicy(session)
    user_project_ids = await policy.get_user_project_ids(user.id)
    entity = await EntityService(session).get_by_id(entity_id)
    policy.check_can_mutate_entity(entity.project_id, user, user_project_ids)
    ctx = await ContextService(session).add_context(entity_id, body)
    return OkResponse(data=ContextRead.model_validate(ctx))


@router.get("/entities/{entity_id}/contexts", response_model=OkResponse[list[ContextRead]])
async def list_contexts(
    entity_id: uuid.UUID,
    session: SessionDep,
    user: Annotated[UserAccount | None, Depends(get_optional_user)],
    context_type: ContextType | None = Query(None, description="Filter by context type"),
    language: Locale | None = Query(None, description="Filter by language"),
) -> OkResponse[list[ContextRead]]:
    policy = AccessPolicy(session)
    visible_ids = await policy.get_visible_project_ids(user)
    entity = await EntityService(session).get_by_id(entity_id)
    policy.check_can_view_entity(entity.project_id, user, visible_ids)
    contexts = await ContextService(session).list_contexts(entity_id, context_type, language)
    return OkResponse(data=[ContextRead.model_validate(c) for c in contexts])
