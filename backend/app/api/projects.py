from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import ActorDep, AdminDep
from app.db.session import get_session
from app.domain.schemas import OkResponse
from app.exceptions import RegistryError
from app.service.project_service import ProjectService

router = APIRouter(prefix="/projects", tags=["projects"])

SessionDep = Annotated[AsyncSession, Depends(get_session)]


# ---------------------------------------------------------------------------
# Schemas
# ---------------------------------------------------------------------------


class ProjectCreate(BaseModel):
    id: str
    alias: str
    description: str | None = None


class ProjectRead(BaseModel):
    id: str
    alias: str
    description: str | None
    is_active: bool

    model_config = {"from_attributes": True}


# ---------------------------------------------------------------------------
# Project CRUD (admin only for create)
# ---------------------------------------------------------------------------


@router.post("", status_code=201, response_model=OkResponse[ProjectRead])
async def create_project(
    body: ProjectCreate,
    session: SessionDep,
    _admin: AdminDep,
) -> OkResponse[ProjectRead]:
    project = await ProjectService(session).create_project(
        id=body.id,
        alias=body.alias,
        description=body.description,
    )
    return OkResponse(data=ProjectRead.model_validate(project))


@router.get("", response_model=OkResponse[list[ProjectRead]])
async def list_projects(
    session: SessionDep,
    actor: ActorDep,
) -> OkResponse[list[ProjectRead]]:
    projects = await ProjectService(session).list_projects()
    if not actor.is_admin:
        projects = [p for p in projects if p.id == actor.api_key.project_id]
    return OkResponse(data=[ProjectRead.model_validate(p) for p in projects])


@router.get("/{project_id}", response_model=OkResponse[ProjectRead])
async def get_project(
    project_id: str,
    session: SessionDep,
    actor: ActorDep,
) -> OkResponse[ProjectRead]:
    if not actor.is_admin and project_id != actor.api_key.project_id:
        raise RegistryError("FORBIDDEN", "API key restricted to a different project", status_code=403)
    project = await ProjectService(session).get_project(project_id)
    return OkResponse(data=ProjectRead.model_validate(project))
