from __future__ import annotations

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, Response
from pydantic import BaseModel, EmailStr
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import get_actor, get_current_admin, get_current_user
from app.db.session import get_session
from app.domain.models import ApiKey, UserAccount
from app.domain.schemas import OkResponse
from app.repository.project_member_repository import ProjectMemberRepository
from app.repository.project_repository import ProjectRepository
from app.service.auth_service import AuthService

router = APIRouter(prefix="/auth", tags=["auth"])

_COOKIE_NAME = "access_token"
_COOKIE_MAX_AGE = 60 * 60 * 24 * 7  # 7 days


# ---------------------------------------------------------------------------
# Request / response schemas
# ---------------------------------------------------------------------------


class LoginRequest(BaseModel):
    email: str
    password: str


class UserRead(BaseModel):
    id: uuid.UUID
    email: str
    display_name: str
    role: str
    is_active: bool

    model_config = {"from_attributes": True}


class UserCreateRequest(BaseModel):
    email: str
    password: str
    display_name: str
    role: str = "user"


class ApiKeyCreateRequest(BaseModel):
    name: str
    scopes: list[str]
    project_id: str | None = None


class ApiKeyRead(BaseModel):
    id: uuid.UUID
    name: str
    scopes: list[str]
    project_id: str | None
    project_name: str | None = None
    is_legacy: bool = False
    created_at: str
    revoked_at: str | None = None
    is_active: bool = True

    model_config = {"from_attributes": True}

    @classmethod
    def from_orm_model(
        cls,
        key: "ApiKey",
        project_name: str | None = None,
        owner_role: str | None = None,
    ) -> "ApiKeyRead":
        is_legacy = key.project_id is None and (owner_role is None or owner_role != "admin")
        return cls(
            id=key.id,
            name=key.name,
            scopes=key.scopes,
            project_id=key.project_id,
            project_name=project_name,
            is_legacy=is_legacy,
            created_at=key.created_at.isoformat(),
            revoked_at=key.revoked_at.isoformat() if key.revoked_at else None,
            is_active=key.revoked_at is None,
        )


class AdminApiKeyRead(ApiKeyRead):
    created_by_email: str | None = None

    @classmethod
    def from_orm_with_email(
        cls,
        key: "ApiKey",
        email: str | None,
        project_name: str | None = None,
        owner_role: str | None = None,
    ) -> "AdminApiKeyRead":
        is_legacy = key.project_id is None and (owner_role is None or owner_role != "admin")
        return cls(
            id=key.id,
            name=key.name,
            scopes=key.scopes,
            project_id=key.project_id,
            project_name=project_name,
            is_legacy=is_legacy,
            created_at=key.created_at.isoformat(),
            revoked_at=key.revoked_at.isoformat() if key.revoked_at else None,
            is_active=key.revoked_at is None,
            created_by_email=email,
        )


class ApiKeyCreatedResponse(BaseModel):
    id: uuid.UUID
    name: str
    scopes: list[str]
    key: str  # raw key — shown only once


SessionDep = Annotated[AsyncSession, Depends(get_session)]


# ---------------------------------------------------------------------------
# Login / logout / me
# ---------------------------------------------------------------------------


@router.post("/login", response_model=OkResponse[UserRead])
async def login(body: LoginRequest, response: Response, session: SessionDep) -> OkResponse[UserRead]:
    user, token = await AuthService(session).login(body.email, body.password)
    response.set_cookie(
        key=_COOKIE_NAME,
        value=token,
        httponly=True,
        samesite="lax",
        max_age=_COOKIE_MAX_AGE,
        secure=False,  # set True behind HTTPS in production
    )
    return OkResponse(data=UserRead.model_validate(user))


@router.post("/logout", response_model=OkResponse[dict])
async def logout(response: Response) -> OkResponse[dict]:
    response.delete_cookie(key=_COOKIE_NAME, httponly=True, samesite="lax")
    return OkResponse(data={"message": "logged out"})


@router.get("/me", response_model=OkResponse[UserRead])
async def me(user: Annotated[UserAccount, Depends(get_current_user)]) -> OkResponse[UserRead]:
    return OkResponse(data=UserRead.model_validate(user))


# ---------------------------------------------------------------------------
# User management (admin only)
# ---------------------------------------------------------------------------


@router.post("/users", status_code=201, response_model=OkResponse[UserRead])
async def create_user(
    body: UserCreateRequest,
    session: SessionDep,
    admin: Annotated[UserAccount, Depends(get_current_admin)],
) -> OkResponse[UserRead]:
    user = await AuthService(session).create_user(
        email=body.email,
        password=body.password,
        display_name=body.display_name,
        role=body.role,
        created_by=admin.id,
    )
    return OkResponse(data=UserRead.model_validate(user))


# ---------------------------------------------------------------------------
# API Key management (logged-in users + admin)
# ---------------------------------------------------------------------------


@router.post("/api-keys", status_code=201, response_model=OkResponse[ApiKeyCreatedResponse])
async def create_api_key(
    body: ApiKeyCreateRequest,
    session: SessionDep,
    user: Annotated[UserAccount, Depends(get_current_user)],
) -> OkResponse[ApiKeyCreatedResponse]:
    from app.exceptions import RegistryError as _Err
    if user.role != "admin":
        if body.project_id is None:
            raise _Err("PROJECT_REQUIRED", "project_id is required for non-admin users", status_code=422)
        proj = await ProjectRepository(session).get_by_id(body.project_id)
        if proj is None:
            raise _Err("NOT_FOUND", f"Project '{body.project_id}' not found", status_code=404)
        member_repo = ProjectMemberRepository(session)
        member_ids = await member_repo.get_project_ids_for_user(user.id)
        if body.project_id not in member_ids:
            raise _Err("FORBIDDEN", "Not a member of this project", status_code=403)

    api_key, raw_key = await AuthService(session).create_api_key(
        name=body.name,
        scopes=body.scopes,
        project_id=body.project_id,
        created_by=user.id,
    )
    return OkResponse(
        data=ApiKeyCreatedResponse(
            id=api_key.id,
            name=api_key.name,
            scopes=api_key.scopes,
            key=raw_key,
        )
    )


@router.get("/api-keys", response_model=OkResponse[list[ApiKeyRead]])
async def list_my_api_keys(
    session: SessionDep,
    user: Annotated[UserAccount, Depends(get_current_user)],
) -> OkResponse[list[ApiKeyRead]]:
    rows = await AuthService(session).list_api_keys(user.id)
    return OkResponse(data=[ApiKeyRead.from_orm_model(k, project_name=pn, owner_role=role) for k, pn, role in rows])


@router.delete("/api-keys/{key_id}", status_code=200, response_model=OkResponse[ApiKeyRead])
async def revoke_api_key(
    key_id: uuid.UUID,
    session: SessionDep,
    user: Annotated[UserAccount, Depends(get_current_user)],
) -> OkResponse[ApiKeyRead]:
    key = await AuthService(session).revoke_api_key(
        key_id,
        actor_id=user.id,
        is_admin=user.role == "admin",
    )
    return OkResponse(data=ApiKeyRead.from_orm_model(key))
