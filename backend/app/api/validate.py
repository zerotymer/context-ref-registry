from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_session
from app.service.validate_service import ValidateService

router = APIRouter(tags=["validate"])

SessionDep = Annotated[AsyncSession, Depends(get_session)]


class ValidateReferencesRequest(BaseModel):
    references: list[str]


@router.post("/validate-references")
async def validate_references(
    body: ValidateReferencesRequest,
    session: SessionDep,
) -> dict:
    result = await ValidateService(session).validate_references(body.references)
    return {
        "ok": True,
        "data": {
            "valid": result.valid,
            "resolved": result.resolved,
            "ambiguous": result.ambiguous,
            "missing": result.missing,
        },
    }
