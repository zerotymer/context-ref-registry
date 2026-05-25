from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_session
from app.domain.schemas import ContextBundleRequest, ContextBundleResponse, OkResponse
from app.service.bundle_service import BundleService

router = APIRouter(tags=["bundle"])

SessionDep = Annotated[AsyncSession, Depends(get_session)]


@router.post("/context-bundle", response_model=OkResponse[ContextBundleResponse])
async def get_context_bundle(
    body: ContextBundleRequest,
    session: SessionDep,
) -> OkResponse[ContextBundleResponse]:
    bundle = await BundleService(session).get_context_bundle(body)
    return OkResponse(data=bundle)
