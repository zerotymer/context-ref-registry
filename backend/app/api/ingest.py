from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import get_actor, get_current_user
from app.service.audit_service import actor_identifier
from app.auth.policy import AccessPolicy
from app.db.session import get_session
from app.domain.schemas import BatchIngestRequest, BatchIngestResult, OkResponse
from app.service.ingest_service import IngestService

router = APIRouter(tags=["ingest"])

SessionDep = Annotated[AsyncSession, Depends(get_session)]


@router.post("/ingest/batch", status_code=200, response_model=OkResponse[BatchIngestResult])
async def batch_ingest(
    body: BatchIngestRequest,
    session: SessionDep,
    auth: Annotated[tuple, Depends(get_actor)],
) -> OkResponse[BatchIngestResult]:
    user, api_key = auth
    policy = AccessPolicy(session)
    for item in body.entities:
        project_id = getattr(item, "project_id", None)
        await policy.check_can_assign_project(project_id, user)
        if api_key is not None:
            user_project_ids = await policy.get_user_project_ids(user.id)
            policy.check_can_mutate_entity(
                str(project_id) if project_id else None, user, user_project_ids, api_key
            )
    actor = actor_identifier(user, api_key)
    result = await IngestService(session).batch_ingest(body, actor=actor)
    return OkResponse(data=result)
