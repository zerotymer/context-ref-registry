from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import get_optional_user
from app.auth.policy import AccessPolicy
from app.db.session import get_session
from app.domain.enums import EntityType
from app.domain.models import UserAccount
from app.domain.schemas import EntityRead, OkResponse
from app.repository.entity_repository import EntityRepository
from app.service.embedding_service import get_embedding_service

router = APIRouter(tags=["search"])

SessionDep = Annotated[AsyncSession, Depends(get_session)]


class SearchResult(EntityRead):
    match_reason: str


@router.get("/search", response_model=OkResponse[list[SearchResult]])
async def search_entities(
    session: SessionDep,
    user: Annotated[UserAccount | None, Depends(get_optional_user)],
    q: str = Query(..., min_length=1, description="검색 쿼리"),
    types: list[EntityType] | None = Query(None, description="entity type 필터"),
    tags: list[str] | None = Query(None, description="AND 필터 — 지정한 태그를 모두 가진 entity만 반환"),
    limit: int = Query(10, ge=1, le=100),
):
    """entity를 alias exact → canonical_name partial → vector 순으로 검색한다."""
    visible_ids = await AccessPolicy(session).get_visible_project_ids(user)
    repo = EntityRepository(session)
    hits = await repo.search(q, types, tags, limit, visible_project_ids=visible_ids)

    results = [
        SearchResult(**EntityRead.model_validate(entity).model_dump(), match_reason=reason)
        for entity, reason in hits
    ]

    # vector search fallback — only when keyword search did not fill the limit
    remaining = limit - len(results)
    if remaining > 0:
        emb_svc = get_embedding_service()
        if emb_svc.enabled:
            embedding = await emb_svc.embed(q)
            if embedding:
                seen_ids = {r.id for r in results}
                vector_hits = await repo.search_by_vector(
                    embedding, types, tags, remaining, visible_project_ids=visible_ids, exclude_ids=seen_ids
                )
                for entity, reason, _dist in vector_hits:
                    results.append(
                        SearchResult(**EntityRead.model_validate(entity).model_dump(), match_reason=reason)
                    )

    return OkResponse(data=results)
