from __future__ import annotations

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_session
from app.domain.enums import ContextType, Locale
from app.domain.schemas import ContextCreate, ContextRead, OkResponse
from app.service.context_service import ContextService

router = APIRouter(tags=["contexts"])

SessionDep = Annotated[AsyncSession, Depends(get_session)]


@router.post("/entities/{entity_id}/contexts", status_code=201, response_model=OkResponse[ContextRead])
async def add_context(
    entity_id: uuid.UUID,
    body: ContextCreate,
    session: SessionDep,
) -> OkResponse[ContextRead]:
    ctx = await ContextService(session).add_context(entity_id, body)
    return OkResponse(data=ContextRead.model_validate(ctx))


@router.get("/entities/{entity_id}/contexts", response_model=OkResponse[list[ContextRead]])
async def list_contexts(
    entity_id: uuid.UUID,
    session: SessionDep,
    context_type: ContextType | None = Query(None, description="Filter by context type"),
    language: Locale | None = Query(None, description="Filter by language"),
) -> OkResponse[list[ContextRead]]:
    contexts = await ContextService(session).list_contexts(entity_id, context_type, language)
    return OkResponse(data=[ContextRead.model_validate(c) for c in contexts])
