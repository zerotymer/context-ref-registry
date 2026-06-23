from __future__ import annotations

from typing import Annotated, Literal

from fastapi import APIRouter, Body, Depends, Header, Query
from fastapi.responses import HTMLResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import get_actor, get_optional_actor
from app.exceptions import RegistryError
from app.service.audit_service import actor_identifier
from app.service.mockup_service import render_mockup
from app.auth.policy import AccessPolicy
from app.db.session import get_session
from app.domain.enums import EntityStatus, EntityType
from app.domain.schemas import (
    BatchCreateItem,
    EntityBatchCreateRequest,
    EntityBatchCreateResult,
    EntityCreate,
    EntityHistoryListResponse,
    EntityHistoryRead,
    EntityListResponse,
    EntityRead,
    EntityUpdate,
    OkResponse,
    RevisionCompareResponse,
    TagRead,
)
from app.service.entity_service import EntityService

router = APIRouter(prefix="/entities", tags=["entities"])

SessionDep = Annotated[AsyncSession, Depends(get_session)]


@router.get("", response_model=OkResponse[EntityListResponse])
async def list_entities(
    session: SessionDep,
    auth: Annotated[tuple, Depends(get_optional_actor)],
    status: EntityStatus | None = Query(None),
    types: list[EntityType] | None = Query(None),
    tags: list[str] | None = Query(None, description="AND 필터 — 지정한 태그를 모두 가진 entity만 반환"),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    sort: Literal["created_at", "updated_at", "canonical_name"] = Query("created_at"),
    order: Literal["asc", "desc"] = Query("desc"),
    project_id: str | None = Query(None, description="프로젝트 ID로 필터"),
) -> OkResponse[EntityListResponse]:
    user, api_key = auth
    visible_ids = await AccessPolicy(session).get_visible_project_ids(user, api_key)
    items, total = await EntityService(session).list(
        status, types, tags, limit, offset, sort, order, visible_project_ids=visible_ids, project_id=project_id
    )
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
    auth: Annotated[tuple, Depends(get_actor)],
    x_changed_by: str | None = Header(default=None),
) -> OkResponse[dict[str, str]]:
    user, api_key = auth
    policy = AccessPolicy(session)
    await policy.check_can_assign_project(body.project_id, user)
    actor = actor_identifier(user, api_key)
    entity = await EntityService(session).create(body, changed_by=x_changed_by or actor)
    return OkResponse(data={"id": str(entity.id)})


@router.post("/batch", status_code=207, response_model=OkResponse[EntityBatchCreateResult])
async def batch_create_entities(
    body: EntityBatchCreateRequest,
    session: SessionDep,
    auth: Annotated[tuple, Depends(get_actor)],
    x_changed_by: str | None = Header(default=None),
) -> OkResponse[EntityBatchCreateResult]:
    user, api_key = auth
    policy = AccessPolicy(session)
    for item in body.entities:
        await policy.check_can_assign_project(item.project_id, user)
    actor = actor_identifier(user, api_key)
    items = await EntityService(session).batch_create(body.entities, changed_by=x_changed_by or actor)
    created = sum(1 for i in items if i.ok)
    failed = len(items) - created
    return OkResponse(data=EntityBatchCreateResult(
        total=len(items), created=created, failed=failed, items=items
    ))


@router.get("/{entity_ref}", response_model=OkResponse[EntityRead])
async def get_entity(
    entity_ref: str,
    session: SessionDep,
    auth: Annotated[tuple, Depends(get_optional_actor)],
) -> OkResponse[EntityRead]:
    user, api_key = auth
    policy = AccessPolicy(session)
    visible_ids = await policy.get_visible_project_ids(user, api_key)
    entity = await EntityService(session).resolve_ref(entity_ref)
    policy.check_can_view_entity(entity.project_id, user, visible_ids)
    return OkResponse(data=EntityRead.model_validate(entity))


@router.patch("/{entity_ref}", response_model=OkResponse[EntityRead])
async def update_entity(
    entity_ref: str,
    body: EntityUpdate,
    session: SessionDep,
    auth: Annotated[tuple, Depends(get_actor)],
    x_changed_by: str | None = Header(default=None),
) -> OkResponse[EntityRead]:
    user, api_key = auth
    policy = AccessPolicy(session)
    user_project_ids = await policy.get_user_project_ids(user.id)
    entity = await EntityService(session).resolve_ref(entity_ref)
    policy.check_can_mutate_entity(entity.project_id, user, user_project_ids, api_key)
    actor = actor_identifier(user, api_key)
    entity = await EntityService(session).update(entity.id, body, changed_by=x_changed_by or actor)
    return OkResponse(data=EntityRead.model_validate(entity))


@router.get("/{entity_ref}/mockup", response_class=HTMLResponse)
async def get_entity_mockup(
    entity_ref: str,
    session: SessionDep,
    auth: Annotated[tuple, Depends(get_optional_actor)],
) -> HTMLResponse:
    """Render a UI_AREA entity's metadata into a standalone mockup HTML document."""
    user, api_key = auth
    policy = AccessPolicy(session)
    visible_ids = await policy.get_visible_project_ids(user, api_key)
    entity = await EntityService(session).resolve_ref(entity_ref)
    # Hide out-of-scope entities as 404 (do not leak existence via 403).
    if (
        entity.project_id is not None
        and visible_ids is not None
        and entity.project_id not in visible_ids
    ):
        raise RegistryError("ENTITY_NOT_FOUND", "Entity not found", status_code=404)
    if entity.type != EntityType.UI_AREA.value:
        raise RegistryError("NOT_A_UI_AREA", "Mockup is only available for UI_AREA entities", status_code=400)
    return HTMLResponse(render_mockup(entity))


# ---------------------------------------------------------------------------
# Tag sub-endpoints
# ---------------------------------------------------------------------------


@router.get("/{entity_ref}/tags", response_model=OkResponse[list[str]])
async def list_entity_tags(
    entity_ref: str,
    session: SessionDep,
    auth: Annotated[tuple, Depends(get_optional_actor)],
) -> OkResponse[list[str]]:
    user, api_key = auth
    policy = AccessPolicy(session)
    visible_ids = await policy.get_visible_project_ids(user, api_key)
    entity = await EntityService(session).resolve_ref(entity_ref)
    policy.check_can_view_entity(entity.project_id, user, visible_ids)
    return OkResponse(data=[t.tag for t in entity.tags])


@router.post("/{entity_ref}/tags", status_code=201, response_model=OkResponse[list[str]])
async def add_entity_tag(
    entity_ref: str,
    session: SessionDep,
    auth: Annotated[tuple, Depends(get_actor)],
    tag: str = Body(..., embed=True),
) -> OkResponse[list[str]]:
    user, api_key = auth
    policy = AccessPolicy(session)
    user_project_ids = await policy.get_user_project_ids(user.id)
    entity = await EntityService(session).resolve_ref(entity_ref)
    policy.check_can_mutate_entity(entity.project_id, user, user_project_ids, api_key)
    entity = await EntityService(session).add_tag(entity.id, tag)
    return OkResponse(data=[t.tag for t in entity.tags])


@router.delete("/{entity_ref}/tags/{tag}", status_code=200, response_model=OkResponse[dict])
async def remove_entity_tag(
    entity_ref: str,
    tag: str,
    session: SessionDep,
    auth: Annotated[tuple, Depends(get_actor)],
) -> OkResponse[dict]:
    user, api_key = auth
    policy = AccessPolicy(session)
    user_project_ids = await policy.get_user_project_ids(user.id)
    entity = await EntityService(session).resolve_ref(entity_ref)
    policy.check_can_mutate_entity(entity.project_id, user, user_project_ids, api_key)
    await EntityService(session).remove_tag(entity.id, tag)
    return OkResponse(data={"removed": tag})


# ---------------------------------------------------------------------------
# History sub-endpoints
# ---------------------------------------------------------------------------


@router.get("/{entity_ref}/history", response_model=OkResponse[EntityHistoryListResponse])
async def list_entity_history(
    entity_ref: str,
    session: SessionDep,
    auth: Annotated[tuple, Depends(get_optional_actor)],
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
) -> OkResponse[EntityHistoryListResponse]:
    user, api_key = auth
    policy = AccessPolicy(session)
    visible_ids = await policy.get_visible_project_ids(user, api_key)
    entity = await EntityService(session).resolve_ref(entity_ref)
    policy.check_can_view_entity(entity.project_id, user, visible_ids)
    items, total = await EntityService(session).list_history(entity.id, limit, offset)
    return OkResponse(data=EntityHistoryListResponse(
        items=[EntityHistoryRead.model_validate(h) for h in items],
        total=total,
    ))


@router.get("/{entity_ref}/history/{revision_no}", response_model=OkResponse[EntityHistoryRead])
async def get_entity_history_revision(
    entity_ref: str,
    revision_no: int,
    session: SessionDep,
    auth: Annotated[tuple, Depends(get_optional_actor)],
) -> OkResponse[EntityHistoryRead]:
    user, api_key = auth
    policy = AccessPolicy(session)
    visible_ids = await policy.get_visible_project_ids(user, api_key)
    entity = await EntityService(session).resolve_ref(entity_ref)
    policy.check_can_view_entity(entity.project_id, user, visible_ids)
    history = await EntityService(session).get_history_revision(entity.id, revision_no)
    return OkResponse(data=EntityHistoryRead.model_validate(history))


@router.get("/{entity_ref}/history/{rev_a}/compare/{rev_b}", response_model=OkResponse[RevisionCompareResponse])
async def compare_entity_history(
    entity_ref: str,
    rev_a: int,
    rev_b: int,
    session: SessionDep,
    auth: Annotated[tuple, Depends(get_optional_actor)],
) -> OkResponse[RevisionCompareResponse]:
    user, api_key = auth
    policy = AccessPolicy(session)
    visible_ids = await policy.get_visible_project_ids(user, api_key)
    entity = await EntityService(session).resolve_ref(entity_ref)
    policy.check_can_view_entity(entity.project_id, user, visible_ids)
    result = await EntityService(session).compare_revisions(entity.id, rev_a, rev_b)
    return OkResponse(data=result)
