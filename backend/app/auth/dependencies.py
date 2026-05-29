from __future__ import annotations

from typing import Annotated

from fastapi import Cookie, Depends, Header
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_session
from app.domain.models import ApiKey, UserAccount
from app.exceptions import RegistryError
from app.service.auth_service import AuthService

_COOKIE_NAME = "access_token"


async def _resolve_actor(
    session: AsyncSession,
    access_token: str | None,
    authorization: str | None,
    *,
    raise_on_missing: bool,
) -> tuple[UserAccount | None, ApiKey | None]:
    svc = AuthService(session)

    if access_token:
        user = await svc.get_user_by_token(access_token)
        return user, None

    if authorization and authorization.startswith("Bearer "):
        raw_key = authorization.removeprefix("Bearer ").strip()
        user, api_key = await svc.get_user_by_api_key(raw_key)
        return user, api_key

    if raise_on_missing:
        raise RegistryError("UNAUTHORIZED", "Authentication required", status_code=401)
    return None, None


async def _get_current_actor(
    session: Annotated[AsyncSession, Depends(get_session)],
    access_token: Annotated[str | None, Cookie(alias=_COOKIE_NAME)] = None,
    authorization: Annotated[str | None, Header()] = None,
) -> tuple[UserAccount | None, ApiKey | None]:
    return await _resolve_actor(session, access_token, authorization, raise_on_missing=True)


async def _get_optional_actor(
    session: Annotated[AsyncSession, Depends(get_session)],
    access_token: Annotated[str | None, Cookie(alias=_COOKIE_NAME)] = None,
    authorization: Annotated[str | None, Header()] = None,
) -> tuple[UserAccount | None, ApiKey | None]:
    return await _resolve_actor(session, access_token, authorization, raise_on_missing=False)


async def get_current_user(
    actor: Annotated[tuple, Depends(_get_current_actor)],
) -> UserAccount:
    """Require an authenticated user (cookie session or API key with an owner)."""
    user, _ = actor
    if user is None:
        raise RegistryError("UNAUTHORIZED", "Authentication required", status_code=401)
    return user


async def get_optional_user(
    actor: Annotated[tuple, Depends(_get_optional_actor)],
) -> UserAccount | None:
    """Return the authenticated user or None if not authenticated."""
    user, _ = actor
    return user


async def get_current_admin(
    user: Annotated[UserAccount, Depends(get_current_user)],
) -> UserAccount:
    if user.role != "admin":
        raise RegistryError("FORBIDDEN", "Admin access required", status_code=403)
    return user


async def get_actor(
    actor: Annotated[tuple, Depends(_get_current_actor)],
) -> tuple[UserAccount | None, ApiKey | None]:
    """Accept either user session or API key. Returns (user, api_key)."""
    return actor
