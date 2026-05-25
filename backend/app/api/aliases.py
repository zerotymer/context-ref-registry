from __future__ import annotations

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_session
from app.domain.enums import EntityType, Locale
from app.domain.schemas import AliasCreate, AliasRead, OkResponse, ResolveResult
from app.service.alias_service import AliasService

router = APIRouter(tags=["aliases"])

SessionDep = Annotated[AsyncSession, Depends(get_session)]


@router.post("/entities/{entity_id}/aliases", status_code=201, response_model=OkResponse[AliasRead])
async def add_alias(
    entity_id: uuid.UUID,
    body: AliasCreate,
    session: SessionDep,
) -> OkResponse[AliasRead]:
    alias = await AliasService(session).add_alias(entity_id, body)
    return OkResponse(data=AliasRead.model_validate(alias))


@router.get("/entities/{entity_id}/aliases", response_model=OkResponse[list[AliasRead]])
async def list_aliases(
    entity_id: uuid.UUID,
    session: SessionDep,
) -> OkResponse[list[AliasRead]]:
    aliases = await AliasService(session).list_aliases(entity_id)
    return OkResponse(data=[AliasRead.model_validate(a) for a in aliases])


@router.get("/resolve", response_model=OkResponse[ResolveResult])
async def resolve_alias(
    session: SessionDep,
    alias: str = Query(..., description="Alias string to resolve"),
    locale: Locale | None = Query(None, description="Filter by locale"),
    type: EntityType | None = Query(None, description="Filter by entity type"),
) -> OkResponse[ResolveResult]:
    result = await AliasService(session).resolve(alias, locale, type)
    return OkResponse(data=result)
