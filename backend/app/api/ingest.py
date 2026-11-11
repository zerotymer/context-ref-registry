from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import WriterDep
from app.auth.policy import check_can_assign_project, check_can_mutate_entity
from app.db.session import get_session
from app.domain.models import Entity
from app.domain.schemas import BatchIngestRequest, BatchIngestResult, OkResponse
from app.service.audit_service import actor_identifier
from app.service.ingest_service import IngestService

router = APIRouter(tags=["ingest"])

SessionDep = Annotated[AsyncSession, Depends(get_session)]


@router.post("/ingest/batch", status_code=200, response_model=OkResponse[BatchIngestResult])
async def batch_ingest(
    body: BatchIngestRequest,
    session: SessionDep,
    actor: WriterDep,
) -> OkResponse[BatchIngestResult]:
    for item in body.entities:
        await check_can_assign_project(session, item.project_id, actor)
    if not actor.is_admin:
        # Upsert-by-id and relation sources must not reach outside the key's project.
        ids = {item.id for item in body.entities if item.id} | {r.from_entity_id for r in body.relations}
        for entity_id in ids:
            existing = await session.get(Entity, entity_id)
            if existing is not None:
                check_can_mutate_entity(existing.project_id, actor)
    result = await IngestService(session).batch_ingest(body, actor=actor_identifier(actor))
    return OkResponse(data=result)
