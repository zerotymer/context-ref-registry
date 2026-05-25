from __future__ import annotations

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_session
from app.domain.enums import RelationType
from app.domain.schemas import OkResponse, RelationCreate, RelationRead
from app.exceptions import RegistryError
from app.service.relation_service import RelationService

router = APIRouter(tags=["relations"])

SessionDep = Annotated[AsyncSession, Depends(get_session)]

_VALID_DIRECTIONS = {"out", "in", "both"}


@router.post("/relations", status_code=201, response_model=OkResponse[RelationRead])
async def create_relation(
    body: RelationCreate,
    session: SessionDep,
) -> OkResponse[RelationRead]:
    relation = await RelationService(session).create_relation(body)
    return OkResponse(data=RelationRead.model_validate(relation))


@router.get("/entities/{entity_id}/relations", response_model=OkResponse[list[RelationRead]])
async def list_relations(
    entity_id: uuid.UUID,
    session: SessionDep,
    direction: str = Query("both", description="Traversal direction: out, in, or both"),
    relation_type: RelationType | None = Query(None, description="Filter by relation type"),
    max_depth: int = Query(1, ge=1, le=10, description="Maximum traversal depth"),
) -> OkResponse[list[RelationRead]]:
    if direction not in _VALID_DIRECTIONS:
        raise RegistryError(
            code="INVALID_DIRECTION",
            message=f"direction must be one of: {', '.join(sorted(_VALID_DIRECTIONS))}",
            status_code=400,
        )
    relations = await RelationService(session).list_relations(entity_id, direction, relation_type, max_depth)
    return OkResponse(data=[RelationRead.model_validate(r) for r in relations])
