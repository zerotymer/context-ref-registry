from __future__ import annotations

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.auth import AdminApiKeyRead, ApiKeyCreateRequest, ApiKeyCreatedResponse
from app.auth.dependencies import get_current_admin
from app.db.session import get_session
from app.domain.models import UserAccount
from app.domain.schemas import OkResponse
from app.service.auth_service import AuthService

router = APIRouter(prefix="/admin/api-keys", tags=["admin"])

SessionDep = Annotated[AsyncSession, Depends(get_session)]


@router.get("", response_model=OkResponse[list[AdminApiKeyRead]])
async def list_all_api_keys(
    session: SessionDep,
    admin: Annotated[UserAccount, Depends(get_current_admin)],
    search: str | None = Query(default=None, description="Filter by owner email"),
    is_active: bool | None = Query(default=None),
) -> OkResponse[list[AdminApiKeyRead]]:
    pairs = await AuthService(session).list_all_api_keys(
        created_by_email=search,
        is_active=is_active,
    )
    return OkResponse(data=[AdminApiKeyRead.from_orm_with_email(k, email) for k, email in pairs])


@router.post("", status_code=201, response_model=OkResponse[ApiKeyCreatedResponse])
async def admin_create_api_key(
    body: ApiKeyCreateRequest,
    session: SessionDep,
    admin: Annotated[UserAccount, Depends(get_current_admin)],
) -> OkResponse[ApiKeyCreatedResponse]:
    """Admin creates a key (owned by admin unless project_id specifies otherwise)."""
    api_key, raw_key = await AuthService(session).create_api_key(
        name=body.name,
        scopes=body.scopes,
        project_id=body.project_id,
        created_by=admin.id,
    )
    return OkResponse(
        data=ApiKeyCreatedResponse(
            id=api_key.id,
            name=api_key.name,
            scopes=api_key.scopes,
            key=raw_key,
        )
    )


@router.delete("/{key_id}", status_code=200, response_model=OkResponse[AdminApiKeyRead])
async def admin_revoke_api_key(
    key_id: uuid.UUID,
    session: SessionDep,
    admin: Annotated[UserAccount, Depends(get_current_admin)],
) -> OkResponse[AdminApiKeyRead]:
    key = await AuthService(session).revoke_api_key(
        key_id,
        actor_id=admin.id,
        is_admin=True,
    )
    pairs = await AuthService(session).list_all_api_keys()
    email = next((e for k, e in pairs if k.id == key.id), None)
    return OkResponse(data=AdminApiKeyRead.from_orm_with_email(key, email))
