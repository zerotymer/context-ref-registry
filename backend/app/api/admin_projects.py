from __future__ import annotations

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import get_current_admin
from app.db.session import get_session
from app.domain.models import UserAccount
from app.domain.schemas import OkResponse
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


class MemberRead(BaseModel):
    project_id: str
    user_id: uuid.UUID
    role: str
    is_active: bool

    model_config = {"from_attributes": True}


class MemberCreateRequest(BaseModel):
    user_id: uuid.UUID
    role: str = "member"


class MemberRoleUpdateRequest(BaseModel):
    role: str


# ---------------------------------------------------------------------------
# Projects
# ---------------------------------------------------------------------------


@router.get("", response_model=OkResponse[list[ProjectRead]])
async def list_projects(
    session: SessionDep,
    admin: Annotated[UserAccount, Depends(get_current_admin)],
    is_active: bool | None = Query(default=None),
    search: str | None = Query(default=None),
) -> OkResponse[list[ProjectRead]]:
    projects = await ProjectService(session).list_all_projects(is_active=is_active, search=search)
    return OkResponse(data=[ProjectRead.model_validate(p) for p in projects])


@router.post("", status_code=201, response_model=OkResponse[ProjectRead])
async def create_project(
    body: ProjectCreateRequest,
    session: SessionDep,
    admin: Annotated[UserAccount, Depends(get_current_admin)],
) -> OkResponse[ProjectRead]:
    project = await ProjectService(session).create_project(
        id=body.id,
        alias=body.alias,
        description=body.description,
        created_by=admin.id,
    )
    await AuditLogRepository(session).create(
        actor=str(admin.id),
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
    admin: Annotated[UserAccount, Depends(get_current_admin)],
) -> OkResponse[ProjectRead]:
    svc = ProjectService(session)

    existing = await ProjectRepository(session).get_by_id(project_id)
    if existing is None:
        from app.exceptions import RegistryError
        raise RegistryError("NOT_FOUND", f"Project '{project_id}' not found", status_code=404)

    before_snap = {"alias": existing.alias, "description": existing.description, "is_active": existing.is_active}

    project = await svc.update_project(
        project_id,
        alias=body.alias,
        description=body.description,
        is_active=body.is_active,
    )

    await AuditLogRepository(session).create(
        actor=str(admin.id),
        action="project.update",
        target_type="project",
        target_id=project_id,
        before_snapshot=before_snap,
        after_snapshot={"alias": project.alias, "description": project.description, "is_active": project.is_active},
    )
    await session.commit()
    return OkResponse(data=ProjectRead.model_validate(project))


# ---------------------------------------------------------------------------
# Members (admin only)
# ---------------------------------------------------------------------------


@router.get("/{project_id}/members", response_model=OkResponse[list[MemberRead]])
async def list_members(
    project_id: str,
    session: SessionDep,
    admin: Annotated[UserAccount, Depends(get_current_admin)],
) -> OkResponse[list[MemberRead]]:
    members = await ProjectService(session).list_members(project_id)
    return OkResponse(data=[MemberRead.model_validate(m) for m in members])


@router.post("/{project_id}/members", status_code=201, response_model=OkResponse[MemberRead])
async def add_member(
    project_id: str,
    body: MemberCreateRequest,
    session: SessionDep,
    admin: Annotated[UserAccount, Depends(get_current_admin)],
) -> OkResponse[MemberRead]:
    member = await ProjectService(session).add_member(
        project_id=project_id,
        user_id=body.user_id,
        role=body.role,
        actor_role=admin.role,
        actor_id=admin.id,
    )
    await AuditLogRepository(session).create(
        actor=str(admin.id),
        action="project_member.add",
        target_type="project_member",
        target_id=f"{project_id}:{member.user_id}",
        after_snapshot={"role": member.role, "is_active": member.is_active},
    )
    await session.commit()
    return OkResponse(data=MemberRead.model_validate(member))


@router.patch("/{project_id}/members/{user_id}", response_model=OkResponse[MemberRead])
async def update_member_role(
    project_id: str,
    user_id: uuid.UUID,
    body: MemberRoleUpdateRequest,
    session: SessionDep,
    admin: Annotated[UserAccount, Depends(get_current_admin)],
) -> OkResponse[MemberRead]:
    member = await ProjectService(session).update_member_role(
        project_id=project_id,
        user_id=user_id,
        role=body.role,
        actor_role=admin.role,
    )
    await AuditLogRepository(session).create(
        actor=str(admin.id),
        action="project_member.role_change",
        target_type="project_member",
        target_id=f"{project_id}:{user_id}",
        after_snapshot={"role": body.role},
    )
    await session.commit()
    return OkResponse(data=MemberRead.model_validate(member))


@router.delete("/{project_id}/members/{user_id}", response_model=OkResponse[dict])
async def remove_member(
    project_id: str,
    user_id: uuid.UUID,
    session: SessionDep,
    admin: Annotated[UserAccount, Depends(get_current_admin)],
) -> OkResponse[dict]:
    await ProjectService(session).remove_member(project_id=project_id, user_id=user_id)
    await AuditLogRepository(session).create(
        actor=str(admin.id),
        action="project_member.remove",
        target_type="project_member",
        target_id=f"{project_id}:{user_id}",
    )
    await session.commit()
    return OkResponse(data={"removed": str(user_id)})
