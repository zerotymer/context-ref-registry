from __future__ import annotations

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import get_current_admin, get_current_user
from app.auth.policy import AccessPolicy
from app.db.session import get_session
from app.domain.models import UserAccount
from app.domain.schemas import OkResponse
from app.repository.project_member_repository import ProjectMemberRepository
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


class MemberCreate(BaseModel):
    user_id: uuid.UUID
    role: str = "member"


class MemberRoleUpdate(BaseModel):
    role: str


class MemberRead(BaseModel):
    project_id: str
    user_id: uuid.UUID
    role: str
    is_active: bool

    model_config = {"from_attributes": True}


# ---------------------------------------------------------------------------
# Project CRUD (admin only for create)
# ---------------------------------------------------------------------------


@router.post("", status_code=201, response_model=OkResponse[ProjectRead])
async def create_project(
    body: ProjectCreate,
    session: SessionDep,
    admin: Annotated[UserAccount, Depends(get_current_admin)],
) -> OkResponse[ProjectRead]:
    project = await ProjectService(session).create_project(
        id=body.id,
        alias=body.alias,
        description=body.description,
        created_by=admin.id,
    )
    return OkResponse(data=ProjectRead.model_validate(project))


@router.get("", response_model=OkResponse[list[ProjectRead]])
async def list_projects(
    session: SessionDep,
    _user: Annotated[UserAccount, Depends(get_current_user)],
) -> OkResponse[list[ProjectRead]]:
    projects = await ProjectService(session).list_projects()
    return OkResponse(data=[ProjectRead.model_validate(p) for p in projects])


@router.get("/{project_id}", response_model=OkResponse[ProjectRead])
async def get_project(
    project_id: str,
    session: SessionDep,
    _user: Annotated[UserAccount, Depends(get_current_user)],
) -> OkResponse[ProjectRead]:
    project = await ProjectService(session).get_project(project_id)
    return OkResponse(data=ProjectRead.model_validate(project))


# ---------------------------------------------------------------------------
# Membership management
# ---------------------------------------------------------------------------


@router.get("/{project_id}/members", response_model=OkResponse[list[MemberRead]])
async def list_members(
    project_id: str,
    session: SessionDep,
    user: Annotated[UserAccount, Depends(get_current_user)],
) -> OkResponse[list[MemberRead]]:
    policy = AccessPolicy(session)
    user_project_ids = await policy.get_user_project_ids(user.id)
    user_project_roles = await _get_project_roles(session, user.id)
    policy.check_project_manager(project_id, user, user_project_ids, user_project_roles)

    members = await ProjectService(session).list_members(project_id)
    return OkResponse(data=[MemberRead.model_validate(m) for m in members])


@router.post("/{project_id}/members", status_code=201, response_model=OkResponse[MemberRead])
async def add_member(
    project_id: str,
    body: MemberCreate,
    session: SessionDep,
    user: Annotated[UserAccount, Depends(get_current_user)],
) -> OkResponse[MemberRead]:
    user_project_ids = await AccessPolicy(session).get_user_project_ids(user.id)
    user_project_roles = await _get_project_roles(session, user.id)
    AccessPolicy(session).check_project_manager(project_id, user, user_project_ids, user_project_roles)

    member = await ProjectService(session).add_member(
        project_id=project_id,
        user_id=body.user_id,
        role=body.role,
        actor_role=user.role,
        actor_id=user.id,
    )
    return OkResponse(data=MemberRead.model_validate(member))


@router.put(
    "/{project_id}/members/{user_id}/role",
    response_model=OkResponse[MemberRead],
)
async def update_member_role(
    project_id: str,
    user_id: uuid.UUID,
    body: MemberRoleUpdate,
    session: SessionDep,
    user: Annotated[UserAccount, Depends(get_current_user)],
) -> OkResponse[MemberRead]:
    user_project_ids = await AccessPolicy(session).get_user_project_ids(user.id)
    user_project_roles = await _get_project_roles(session, user.id)
    AccessPolicy(session).check_project_manager(project_id, user, user_project_ids, user_project_roles)

    member = await ProjectService(session).update_member_role(
        project_id=project_id,
        user_id=user_id,
        role=body.role,
        actor_role=user.role,
    )
    return OkResponse(data=MemberRead.model_validate(member))


@router.delete("/{project_id}/members/{user_id}", response_model=OkResponse[dict])
async def remove_member(
    project_id: str,
    user_id: uuid.UUID,
    session: SessionDep,
    user: Annotated[UserAccount, Depends(get_current_user)],
) -> OkResponse[dict]:
    user_project_ids = await AccessPolicy(session).get_user_project_ids(user.id)
    user_project_roles = await _get_project_roles(session, user.id)
    AccessPolicy(session).check_project_manager(project_id, user, user_project_ids, user_project_roles)

    await ProjectService(session).remove_member(project_id=project_id, user_id=user_id)
    return OkResponse(data={"removed": str(user_id)})


# ---------------------------------------------------------------------------
# Helper
# ---------------------------------------------------------------------------


async def _get_project_roles(session: AsyncSession, user_id: uuid.UUID) -> dict[str, str]:
    from sqlalchemy import select
    from app.domain.models import ProjectMember

    result = await session.execute(
        select(ProjectMember.project_id, ProjectMember.role).where(
            ProjectMember.user_id == user_id,
            ProjectMember.is_active.is_(True),
        )
    )
    return {row[0]: row[1] for row in result}
