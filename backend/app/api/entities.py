from __future__ import annotations

import uuid
from typing import Annotated, Literal

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_session
from app.domain.enums import EntityStatus, EntityType
from app.domain.schemas import EntityCreate, EntityListResponse, EntityRead, EntityUpdate, OkResponse
from app.service.entity_service import EntityService

router = APIRouter(prefix="/entities", tags=["entities"])

SessionDep = Annotated[AsyncSession, Depends(get_session)]


@router.get("", response_model=OkResponse[EntityListResponse])
async def list_entities(
    session: SessionDep,
    status: EntityStatus | None = Query(None),
    types: list[EntityType] | None = Query(None),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    sort: Literal["created_at", "updated_at", "canonical_name"] = Query("created_at"),
    order: Literal["asc", "desc"] = Query("desc"),
) -> OkResponse[EntityListResponse]:
    items, total = await EntityService(session).list(status, types, limit, offset, sort, order)
    return OkResponse(data=EntityListResponse(
        items=[EntityRead.model_validate(e) for e in items],
        total=total,
        limit=limit,
        offset=offset,
    ))


@router.post("", status_code=201, response_model=OkResponse[dict[str, str]])
async def create_entity(body: EntityCreate, session: SessionDep) -> OkResponse[dict[str, str]]:
    entity = await EntityService(session).create(body)
    return OkResponse(data={"id": str(entity.id)})


@router.get("/{entity_id}", response_model=OkResponse[EntityRead])
async def get_entity(entity_id: uuid.UUID, session: SessionDep) -> OkResponse[EntityRead]:
    entity = await EntityService(session).get_by_id(entity_id)
    return OkResponse(data=EntityRead.model_validate(entity))


@router.patch("/{entity_id}", response_model=OkResponse[EntityRead])
async def update_entity(
    entity_id: uuid.UUID, body: EntityUpdate, session: SessionDep
) -> OkResponse[EntityRead]:
    entity = await EntityService(session).update(entity_id, body)
    return OkResponse(data=EntityRead.model_validate(entity))
