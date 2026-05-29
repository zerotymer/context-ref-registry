from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import get_current_user
from app.auth.policy import AccessPolicy
from app.db.session import get_session
from app.domain.models import UserAccount
from app.domain.schemas import BatchIngestRequest, BatchIngestResult, OkResponse
from app.service.ingest_service import IngestService

router = APIRouter(tags=["ingest"])

SessionDep = Annotated[AsyncSession, Depends(get_session)]


@router.post("/ingest/batch", status_code=200, response_model=OkResponse[BatchIngestResult])
async def batch_ingest(
    body: BatchIngestRequest,
    session: SessionDep,
    user: Annotated[UserAccount, Depends(get_current_user)],
) -> OkResponse[BatchIngestResult]:
    policy = AccessPolicy(session)
    for item in body.entities:
        project_id = getattr(item, "project_id", None)
        await policy.check_can_assign_project(project_id, user)
    result = await IngestService(session).batch_ingest(body)
    return OkResponse(data=result)
