from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_session
from app.domain.schemas import OkResponse, TagRead
from app.service.entity_service import EntityService

router = APIRouter(tags=["tags"])

SessionDep = Annotated[AsyncSession, Depends(get_session)]


@router.get("/tags", response_model=OkResponse[list[TagRead]])
async def list_all_tags(session: SessionDep) -> OkResponse[list[TagRead]]:
    """등록된 모든 태그와 사용 횟수를 반환한다."""
    rows = await EntityService(session).list_all_tags()
    return OkResponse(data=[TagRead(tag=tag, count=count) for tag, count in rows])
