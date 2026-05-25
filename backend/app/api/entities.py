from __future__ import annotations

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_session
from app.domain.schemas import EntityCreate, EntityRead, EntityUpdate, OkResponse
from app.service.entity_service import EntityService

router = APIRouter(prefix="/entities", tags=["entities"])

SessionDep = Annotated[AsyncSession, Depends(get_session)]


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
