from fastapi import APIRouter, Query

from app.db.session import async_session_factory
from app.domain.enums import EntityType
from app.domain.schemas import EntityRead, OkResponse
from app.repository.entity_repository import EntityRepository

router = APIRouter(tags=["search"])


class SearchResult(EntityRead):
    match_reason: str


@router.get("/search", response_model=OkResponse[list[SearchResult]])
async def search_entities(
    q: str = Query(..., min_length=1, description="검색 쿼리"),
    types: list[EntityType] | None = Query(None, description="entity type 필터"),
    tags: list[str] | None = Query(None, description="AND 필터 — 지정한 태그를 모두 가진 entity만 반환"),
    limit: int = Query(10, ge=1, le=100),
):
    """entity를 alias exact → canonical_name partial 순으로 검색한다."""
    async with async_session_factory() as session:
        repo = EntityRepository(session)
        hits = await repo.search(q, types, tags, limit)

    results = [
        SearchResult(**EntityRead.model_validate(entity).model_dump(), match_reason=reason)
        for entity, reason in hits
    ]
    return OkResponse(data=results)
