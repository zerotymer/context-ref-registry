from __future__ import annotations

import uuid
from datetime import datetime
from typing import Annotated, Literal

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import AdminDep
from app.db.session import get_session
from app.domain.models import ApiKey
from app.domain.schemas import OkResponse
from app.exceptions import RegistryError
from app.repository.api_key_repository import ApiKeyRepository
from app.repository.project_repository import ProjectRepository
from app.service.auth_service import AuthService

router = APIRouter(prefix="/admin/api-keys", tags=["admin"])

SessionDep = Annotated[AsyncSession, Depends(get_session)]


class ApiKeyCreateRequest(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    project_id: str
    scope: Literal["read", "write"] = "read"
    expires_at: datetime | None = None


class ApiKeyRead(BaseModel):
    id: uuid.UUID
    name: str
    project_id: str
    project_name: str | None = None
    scope: str
    created_at: datetime
    expires_at: datetime | None
    last_used_at: datetime | None
    revoked_at: datetime | None
    is_active: bool

    @classmethod
    def build(cls, key: ApiKey, project_name: str | None = None) -> ApiKeyRead:
        return cls(
            id=key.id,
            name=key.name,
            project_id=key.project_id,
            project_name=project_name,
            scope=key.scope,
            created_at=key.created_at,
            expires_at=key.expires_at,
            last_used_at=key.last_used_at,
            revoked_at=key.revoked_at,
            is_active=key.revoked_at is None,
        )


class ApiKeyCreatedResponse(ApiKeyRead):
    key: str  # raw key — shown only once


@router.get("", response_model=OkResponse[list[ApiKeyRead]])
async def list_api_keys(
    session: SessionDep,
    _admin: AdminDep,
    project_id: str | None = Query(default=None),
    is_active: bool | None = Query(default=None),
) -> OkResponse[list[ApiKeyRead]]:
    rows = await ApiKeyRepository(session).list_all(project_id=project_id, is_active=is_active)
    return OkResponse(data=[ApiKeyRead.build(k, pn) for k, pn in rows])


@router.post("", status_code=201, response_model=OkResponse[ApiKeyCreatedResponse])
async def create_api_key(
    body: ApiKeyCreateRequest,
    session: SessionDep,
    _admin: AdminDep,
) -> OkResponse[ApiKeyCreatedResponse]:
    project = await ProjectRepository(session).get_by_id(body.project_id)
    if project is None:
        raise RegistryError("NOT_FOUND", f"Project '{body.project_id}' not found", status_code=404)
    key, raw_key = await AuthService(session).create_api_key(
        name=body.name, project_id=body.project_id, scope=body.scope, expires_at=body.expires_at
    )
    read = ApiKeyRead.build(key, project.alias)
    return OkResponse(data=ApiKeyCreatedResponse(**read.model_dump(), key=raw_key))


@router.delete("/{key_id}", response_model=OkResponse[ApiKeyRead])
async def revoke_api_key(key_id: uuid.UUID, session: SessionDep, _admin: AdminDep) -> OkResponse[ApiKeyRead]:
    key = await AuthService(session).revoke_api_key(key_id)
    return OkResponse(data=ApiKeyRead.build(key))
