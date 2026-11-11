"""Authentication dependencies.

Two kinds of callers:
- the single admin, via the ``access_token`` JWT cookie (web console)
- LLM agents, via ``Authorization: Bearer crr_...`` project API keys
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Annotated

from fastapi import Cookie, Depends, Header
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_session
from app.domain.models import ApiKey
from app.exceptions import RegistryError
from app.service.auth_service import AuthService, verify_access_token

COOKIE_NAME = "access_token"


@dataclass(frozen=True)
class Actor:
    is_admin: bool
    api_key: ApiKey | None = None

    @property
    def can_write(self) -> bool:
        return self.is_admin or (self.api_key is not None and self.api_key.scope == "write")


def bearer_token(authorization: str | None) -> str | None:
    if authorization and authorization[:7].lower() == "bearer ":
        return authorization[7:].strip() or None
    return None


async def get_optional_actor(
    session: Annotated[AsyncSession, Depends(get_session)],
    access_token: Annotated[str | None, Cookie(alias=COOKIE_NAME)] = None,
    authorization: Annotated[str | None, Header()] = None,
) -> Actor | None:
    """Resolve the caller; None when no credentials were sent."""
    if access_token:
        verify_access_token(access_token)
        return Actor(is_admin=True)
    raw_key = bearer_token(authorization)
    if raw_key:
        return Actor(is_admin=False, api_key=await AuthService(session).get_api_key(raw_key))
    return None


async def get_actor(actor: Annotated[Actor | None, Depends(get_optional_actor)]) -> Actor:
    if actor is None:
        raise RegistryError("UNAUTHORIZED", "Authentication required", status_code=401)
    return actor


async def require_admin(actor: Annotated[Actor, Depends(get_actor)]) -> Actor:
    if not actor.is_admin:
        raise RegistryError("FORBIDDEN", "Admin access required", status_code=403)
    return actor


async def require_write(actor: Annotated[Actor, Depends(get_actor)]) -> Actor:
    if not actor.can_write:
        raise RegistryError("FORBIDDEN", "API key scope 'write' required", status_code=403)
    return actor


OptionalActorDep = Annotated[Actor | None, Depends(get_optional_actor)]
ActorDep = Annotated[Actor, Depends(get_actor)]
AdminDep = Annotated[Actor, Depends(require_admin)]
WriterDep = Annotated[Actor, Depends(require_write)]
