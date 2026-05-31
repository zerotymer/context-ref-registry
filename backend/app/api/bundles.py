from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_session
from app.domain.schemas import ContextBundleRequest, ContextBundleResponse, OkResponse
from app.service.bundle_service import BundleService
from app.service.entity_service import EntityService

router = APIRouter(tags=["bundle"])

SessionDep = Annotated[AsyncSession, Depends(get_session)]


@router.post("/context-bundle", response_model=OkResponse[ContextBundleResponse])
async def get_context_bundle(
    body: ContextBundleRequest,
    session: SessionDep,
) -> OkResponse[ContextBundleResponse]:
    svc = EntityService(session)
    resolved_ids = []
    for ref in body.root_ids:
        entity = await svc.resolve_ref(ref)
        resolved_ids.append(entity.id)

    resolved_body = ContextBundleRequest(
        root_ids=[str(rid) for rid in resolved_ids],
        include_relations=body.include_relations,
        include_types=body.include_types,
        max_depth=body.max_depth,
        token_budget=body.token_budget,
        language=body.language,
    )
    bundle = await BundleService(session).get_context_bundle(resolved_body)
    return OkResponse(data=bundle)
