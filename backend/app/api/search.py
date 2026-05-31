from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import get_optional_actor
from app.auth.policy import AccessPolicy
from app.db.session import get_session
from app.domain.enums import EntityType
from app.domain.schemas import EntityRead, OkResponse
from app.repository.entity_repository import EntityRepository

router = APIRouter(tags=["search"])

SessionDep = Annotated[AsyncSession, Depends(get_session)]


class SearchResult(EntityRead):
    match_reason: str


@router.get("/search", response_model=OkResponse[list[SearchResult]])
async def search_entities(
    session: SessionDep,
    auth: Annotated[tuple, Depends(get_optional_actor)],
    q: str = Query(..., min_length=1, description="검색 쿼리"),
    types: list[EntityType] | None = Query(None, description="entity type 필터"),
    tags: list[str] | None = Query(None, description="AND 필터 — 지정한 태그를 모두 가진 entity만 반환"),
    limit: int = Query(10, ge=1, le=100),
):
    """entity를 alias exact → canonical_name partial 순으로 검색한다."""
    user, api_key = auth
    visible_ids = await AccessPolicy(session).get_visible_project_ids(user, api_key)
    repo = EntityRepository(session)
    hits = await repo.search(q, types, tags, limit, visible_project_ids=visible_ids)

    results = [
        SearchResult(**EntityRead.model_validate(entity).model_dump(), match_reason=reason)
        for entity, reason in hits
    ]
    return OkResponse(data=results)
