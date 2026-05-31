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
from app.repository.user_repository import UserRepository
from app.service.auth_service import AuthService

router = APIRouter(prefix="/admin/users", tags=["admin"])

SessionDep = Annotated[AsyncSession, Depends(get_session)]


# ---------------------------------------------------------------------------
# Schemas
# ---------------------------------------------------------------------------


class UserRead(BaseModel):
    id: uuid.UUID
    login_id: str
    display_name: str
    role: str
    is_active: bool
    must_change_password: bool

    model_config = {"from_attributes": True}


class UserCreateRequest(BaseModel):
    login_id: str
    password: str
    display_name: str
    role: str = "user"


class UserUpdateRequest(BaseModel):
    display_name: str | None = None
    role: str | None = None
    is_active: bool | None = None


class PasswordResetRequest(BaseModel):
    new_password: str


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------


@router.get("", response_model=OkResponse[list[UserRead]])
async def list_users(
    session: SessionDep,
    admin: Annotated[UserAccount, Depends(get_current_admin)],
    role: str | None = Query(default=None),
    is_active: bool | None = Query(default=None),
    search: str | None = Query(default=None),
) -> OkResponse[list[UserRead]]:
    users = await AuthService(session).list_users(role=role, is_active=is_active, search=search)
    return OkResponse(data=[UserRead.model_validate(u) for u in users])


@router.post("", status_code=201, response_model=OkResponse[UserRead])
async def create_user(
    body: UserCreateRequest,
    session: SessionDep,
    admin: Annotated[UserAccount, Depends(get_current_admin)],
) -> OkResponse[UserRead]:
    svc = AuthService(session)
    user = await svc.create_user(
        login_id=body.login_id,
        password=body.password,
        display_name=body.display_name,
        role=body.role,
        created_by=admin.id,
    )
    await AuditLogRepository(session).create(
        actor=str(admin.id),
        action="user.create",
        target_type="user",
        target_id=str(user.id),
        after_snapshot={"login_id": user.login_id, "role": user.role, "is_active": user.is_active},
    )
    await session.commit()
    return OkResponse(data=UserRead.model_validate(user))


@router.patch("/{user_id}", response_model=OkResponse[UserRead])
async def update_user(
    user_id: uuid.UUID,
    body: UserUpdateRequest,
    session: SessionDep,
    admin: Annotated[UserAccount, Depends(get_current_admin)],
) -> OkResponse[UserRead]:
    existing = await UserRepository(session).get_by_id(user_id)
    if existing is None:
        from app.exceptions import RegistryError
        raise RegistryError("NOT_FOUND", "User not found", status_code=404)

    before_snap = {
        "display_name": existing.display_name,
        "role": existing.role,
        "is_active": existing.is_active,
    }

    user = await AuthService(session).update_user(
        user_id,
        display_name=body.display_name,
        role=body.role,
        is_active=body.is_active,
    )

    await AuditLogRepository(session).create(
        actor=str(admin.id),
        action="user.update",
        target_type="user",
        target_id=str(user_id),
        before_snapshot=before_snap,
        after_snapshot={"display_name": user.display_name, "role": user.role, "is_active": user.is_active},
    )
    await session.commit()
    return OkResponse(data=UserRead.model_validate(user))


@router.post("/{user_id}/reset-password", response_model=OkResponse[dict])
async def reset_password(
    user_id: uuid.UUID,
    body: PasswordResetRequest,
    session: SessionDep,
    admin: Annotated[UserAccount, Depends(get_current_admin)],
) -> OkResponse[dict]:
    await AuthService(session).reset_password(user_id, body.new_password)
    await AuditLogRepository(session).create(
        actor=str(admin.id),
        action="user.reset_password",
        target_type="user",
        target_id=str(user_id),
    )
    await session.commit()
    return OkResponse(data={"reset": str(user_id)})
