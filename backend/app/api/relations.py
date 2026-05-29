from __future__ import annotations

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import get_current_user, get_optional_user
from app.auth.policy import AccessPolicy
from app.db.session import get_session
from app.domain.enums import RelationType
from app.domain.models import UserAccount
from app.domain.schemas import OkResponse, RelationCreate, RelationRead
from app.exceptions import RegistryError
from app.service.entity_service import EntityService
from app.service.relation_service import RelationService

router = APIRouter(tags=["relations"])

SessionDep = Annotated[AsyncSession, Depends(get_session)]

_VALID_DIRECTIONS = {"out", "in", "both"}


@router.post("/relations", status_code=201, response_model=OkResponse[RelationRead])
async def create_relation(
    body: RelationCreate,
    session: SessionDep,
    user: Annotated[UserAccount, Depends(get_current_user)],
) -> OkResponse[RelationRead]:
    policy = AccessPolicy(session)
    user_project_ids = await policy.get_user_project_ids(user.id)

    from_entity = await EntityService(session).get_by_id(body.from_entity_id)
    policy.check_can_mutate_entity(from_entity.project_id, user, user_project_ids)

    relation = await RelationService(session).create_relation(body)
    return OkResponse(data=RelationRead.model_validate(relation))


@router.get("/entities/{entity_id}/relations", response_model=OkResponse[list[RelationRead]])
async def list_relations(
    entity_id: uuid.UUID,
    session: SessionDep,
    user: Annotated[UserAccount | None, Depends(get_optional_user)],
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
    policy = AccessPolicy(session)
    visible_ids = await policy.get_visible_project_ids(user)
    entity = await EntityService(session).get_by_id(entity_id)
    policy.check_can_view_entity(entity.project_id, user, visible_ids)
    relations = await RelationService(session).list_relations(entity_id, direction, relation_type, max_depth)
    return OkResponse(data=[RelationRead.model_validate(r) for r in relations])
