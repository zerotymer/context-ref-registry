from __future__ import annotations

import uuid
from typing import Annotated, Literal

from fastapi import APIRouter, Body, Depends, Header, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_session
from app.domain.enums import EntityStatus, EntityType
from app.domain.schemas import (
    EntityCreate,
    EntityHistoryListResponse,
    EntityHistoryRead,
    EntityListResponse,
    EntityRead,
    EntityUpdate,
    OkResponse,
    TagRead,
)
from app.service.entity_service import EntityService

router = APIRouter(prefix="/entities", tags=["entities"])

SessionDep = Annotated[AsyncSession, Depends(get_session)]


@router.get("", response_model=OkResponse[EntityListResponse])
async def list_entities(
    session: SessionDep,
    status: EntityStatus | None = Query(None),
    types: list[EntityType] | None = Query(None),
    tags: list[str] | None = Query(None, description="AND 필터 — 지정한 태그를 모두 가진 entity만 반환"),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    sort: Literal["created_at", "updated_at", "canonical_name"] = Query("created_at"),
    order: Literal["asc", "desc"] = Query("desc"),
) -> OkResponse[EntityListResponse]:
    items, total = await EntityService(session).list(status, types, tags, limit, offset, sort, order)
    return OkResponse(data=EntityListResponse(
        items=[EntityRead.model_validate(e) for e in items],
        total=total,
        limit=limit,
        offset=offset,
    ))


@router.post("", status_code=201, response_model=OkResponse[dict[str, str]])
async def create_entity(
    body: EntityCreate,
    session: SessionDep,
    x_changed_by: str | None = Header(default=None),
) -> OkResponse[dict[str, str]]:
    entity = await EntityService(session).create(body, changed_by=x_changed_by)
    return OkResponse(data={"id": str(entity.id)})


@router.get("/{entity_id}", response_model=OkResponse[EntityRead])
async def get_entity(entity_id: uuid.UUID, session: SessionDep) -> OkResponse[EntityRead]:
    entity = await EntityService(session).get_by_id(entity_id)
    return OkResponse(data=EntityRead.model_validate(entity))


@router.patch("/{entity_id}", response_model=OkResponse[EntityRead])
async def update_entity(
    entity_id: uuid.UUID,
    body: EntityUpdate,
    session: SessionDep,
    x_changed_by: str | None = Header(default=None),
) -> OkResponse[EntityRead]:
    entity = await EntityService(session).update(entity_id, body, changed_by=x_changed_by)
    return OkResponse(data=EntityRead.model_validate(entity))


# ---------------------------------------------------------------------------
# Tag sub-endpoints
# ---------------------------------------------------------------------------


@router.get("/{entity_id}/tags", response_model=OkResponse[list[str]])
async def list_entity_tags(entity_id: uuid.UUID, session: SessionDep) -> OkResponse[list[str]]:
    entity = await EntityService(session).get_by_id(entity_id)
    return OkResponse(data=[t.tag for t in entity.tags])


@router.post("/{entity_id}/tags", status_code=201, response_model=OkResponse[list[str]])
async def add_entity_tag(
    entity_id: uuid.UUID,
    session: SessionDep,
    tag: str = Body(..., embed=True),
) -> OkResponse[list[str]]:
    entity = await EntityService(session).add_tag(entity_id, tag)
    return OkResponse(data=[t.tag for t in entity.tags])


@router.delete("/{entity_id}/tags/{tag}", status_code=200, response_model=OkResponse[dict])
async def remove_entity_tag(
    entity_id: uuid.UUID, tag: str, session: SessionDep
) -> OkResponse[dict]:
    await EntityService(session).remove_tag(entity_id, tag)
    return OkResponse(data={"removed": tag})


# ---------------------------------------------------------------------------
# History sub-endpoints
# ---------------------------------------------------------------------------


@router.get("/{entity_id}/history", response_model=OkResponse[EntityHistoryListResponse])
async def list_entity_history(
    entity_id: uuid.UUID,
    session: SessionDep,
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
) -> OkResponse[EntityHistoryListResponse]:
    items, total = await EntityService(session).list_history(entity_id, limit, offset)
    return OkResponse(data=EntityHistoryListResponse(
        items=[EntityHistoryRead.model_validate(h) for h in items],
        total=total,
    ))


@router.get("/{entity_id}/history/{revision_no}", response_model=OkResponse[EntityHistoryRead])
async def get_entity_history_revision(
    entity_id: uuid.UUID, revision_no: int, session: SessionDep
) -> OkResponse[EntityHistoryRead]:
    history = await EntityService(session).get_history_revision(entity_id, revision_no)
    return OkResponse(data=EntityHistoryRead.model_validate(history))
