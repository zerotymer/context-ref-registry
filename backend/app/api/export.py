from __future__ import annotations

import json
import uuid
from typing import Annotated

import yaml
from fastapi import APIRouter, Depends, Query
from fastapi.responses import PlainTextResponse, Response
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_session
from app.domain.enums import Locale
from app.service.export_service import ExportService

router = APIRouter(prefix="/export", tags=["export"])

SessionDep = Annotated[AsyncSession, Depends(get_session)]


@router.get("/agents-md", response_class=PlainTextResponse)
async def export_agents_md(
    root_ids: Annotated[str, Query(description="Comma-separated root entity UUIDs")],
    session: SessionDep,
    max_depth: Annotated[int, Query(ge=0, le=10)] = 2,
    token_budget: Annotated[int, Query(ge=100)] = 8000,
    language: Locale = Locale.KO,
) -> str:
    parsed: list[uuid.UUID] = [uuid.UUID(rid.strip()) for rid in root_ids.split(",") if rid.strip()]
    md = await ExportService(session).generate_agents_md(
        root_ids=parsed,
        max_depth=max_depth,
        token_budget=token_budget,
        language=language,
    )
    return md


@router.get("/openapi")
async def export_openapi(
    session: SessionDep,
    format: Annotated[str, Query(pattern="^(json|yaml)$")] = "json",
    include_deprecated: bool = False,
    title: str = "Context Registry — API Entities",
    version: str = "generated",
) -> Response:
    spec = await ExportService(session).generate_openapi(
        include_deprecated=include_deprecated,
        title=title,
        version=version,
    )
    if format == "yaml":
        content = yaml.dump(spec, allow_unicode=True, sort_keys=False)
        return Response(content=content, media_type="application/yaml")
    return Response(content=json.dumps(spec, ensure_ascii=False, indent=2), media_type="application/json")
