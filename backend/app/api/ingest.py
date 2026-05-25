from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_session
from app.domain.schemas import BatchIngestRequest, BatchIngestResult, OkResponse
from app.service.ingest_service import IngestService

router = APIRouter(tags=["ingest"])

SessionDep = Annotated[AsyncSession, Depends(get_session)]


@router.post("/ingest/batch", status_code=200, response_model=OkResponse[BatchIngestResult])
async def batch_ingest(
    body: BatchIngestRequest,
    session: SessionDep,
) -> OkResponse[BatchIngestResult]:
    result = await IngestService(session).batch_ingest(body)
    return OkResponse(data=result)
