from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import AdminDep
from app.db.session import get_session
from app.domain.schemas import OkResponse
from app.exceptions import RegistryError
from app.repository.audit_log_repository import AuditLogRepository
from app.repository.project_repository import ProjectRepository
from app.service.project_service import ProjectService

router = APIRouter(prefix="/admin/projects", tags=["admin"])

SessionDep = Annotated[AsyncSession, Depends(get_session)]


# ---------------------------------------------------------------------------
# Schemas
# ---------------------------------------------------------------------------


class ProjectRead(BaseModel):
    id: str
    alias: str
    description: str | None
    is_active: bool

    model_config = {"from_attributes": True}


class ProjectCreateRequest(BaseModel):
    id: str
    alias: str
    description: str | None = None


class ProjectUpdateRequest(BaseModel):
    alias: str | None = None
    description: str | None = None
    is_active: bool | None = None


# ---------------------------------------------------------------------------
# Projects
# ---------------------------------------------------------------------------


@router.get("", response_model=OkResponse[list[ProjectRead]])
async def list_projects(
    session: SessionDep,
    _admin: AdminDep,
    is_active: bool | None = Query(default=None),
    search: str | None = Query(default=None),
) -> OkResponse[list[ProjectRead]]:
    projects = await ProjectService(session).list_all_projects(is_active=is_active, search=search)
    return OkResponse(data=[ProjectRead.model_validate(p) for p in projects])


@router.post("", status_code=201, response_model=OkResponse[ProjectRead])
async def create_project(
    body: ProjectCreateRequest,
    session: SessionDep,
    _admin: AdminDep,
) -> OkResponse[ProjectRead]:
    project = await ProjectService(session).create_project(
        id=body.id,
        alias=body.alias,
        description=body.description,
    )
    await AuditLogRepository(session).create(
        actor="admin",
        action="project.create",
        target_type="project",
        target_id=project.id,
        after_snapshot={"alias": project.alias, "description": project.description, "is_active": project.is_active},
    )
    await session.commit()
    return OkResponse(data=ProjectRead.model_validate(project))


@router.patch("/{project_id}", response_model=OkResponse[ProjectRead])
async def update_project(
    project_id: str,
    body: ProjectUpdateRequest,
    session: SessionDep,
    _admin: AdminDep,
) -> OkResponse[ProjectRead]:
    svc = ProjectService(session)

    existing = await ProjectRepository(session).get_by_id(project_id)
    if existing is None:
        raise RegistryError("NOT_FOUND", f"Project '{project_id}' not found", status_code=404)

    before_snap = {"alias": existing.alias, "description": existing.description, "is_active": existing.is_active}

    project = await svc.update_project(
        project_id,
        alias=body.alias,
        description=body.description,
        is_active=body.is_active,
    )

    await AuditLogRepository(session).create(
        actor="admin",
        action="project.update",
        target_type="project",
        target_id=project_id,
        before_snapshot=before_snap,
        after_snapshot={"alias": project.alias, "description": project.description, "is_active": project.is_active},
    )
    await session.commit()
    return OkResponse(data=ProjectRead.model_validate(project))
