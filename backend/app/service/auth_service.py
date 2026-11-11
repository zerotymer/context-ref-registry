from __future__ import annotations

import hashlib
import hmac
import secrets
import uuid
from datetime import UTC, datetime, timedelta

import jwt
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import JWT_ALGORITHM, JWT_EXPIRE_MINUTES, JWT_SECRET, settings
from app.domain.models import ApiKey
from app.exceptions import RegistryError
from app.repository.api_key_repository import ApiKeyRepository

ADMIN_SUBJECT = "admin"
API_KEY_PREFIX = "crr_"
VALID_SCOPES = ("read", "write")
# Only write last_used_at when it is older than this, to avoid a write lock on every request.
_LAST_USED_GRANULARITY = timedelta(seconds=60)


def create_access_token() -> str:
    expire = datetime.now(UTC) + timedelta(minutes=JWT_EXPIRE_MINUTES)
    return jwt.encode({"sub": ADMIN_SUBJECT, "exp": expire}, JWT_SECRET, algorithm=JWT_ALGORITHM)


def verify_access_token(token: str) -> None:
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
    except Exception:
        raise RegistryError("UNAUTHORIZED", "Invalid or expired token", status_code=401)
    if payload.get("sub") != ADMIN_SUBJECT:
        raise RegistryError("UNAUTHORIZED", "Invalid or expired token", status_code=401)


def _hash_api_key(raw_key: str) -> str:
    return hashlib.sha256(raw_key.encode()).hexdigest()


def login(login_id: str, password: str) -> str:
    """Check credentials against ADMIN_LOGIN_ID / ADMIN_PASSWORD and return a JWT."""
    if not settings.admin_password:
        raise RegistryError("ADMIN_DISABLED", "ADMIN_PASSWORD is not configured", status_code=503)
    ok_id = hmac.compare_digest(login_id.strip().lower().encode(), settings.admin_login_id.lower().encode())
    ok_pw = hmac.compare_digest(password.encode(), settings.admin_password.encode())
    if not (ok_id and ok_pw):
        raise RegistryError("UNAUTHORIZED", "Invalid credentials", status_code=401)
    return create_access_token()


class AuthService:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._repo = ApiKeyRepository(session)

    async def get_api_key(self, raw_key: str) -> ApiKey:
        """Resolve an active (not revoked, not expired) key; bump last_used_at."""
        api_key = await self._repo.get_by_hash(_hash_api_key(raw_key))
        now = datetime.now(UTC)
        if api_key is None or (api_key.expires_at is not None and api_key.expires_at <= now):
            raise RegistryError("UNAUTHORIZED", "Invalid, expired or revoked API key", status_code=401)
        if api_key.last_used_at is None or now - api_key.last_used_at >= _LAST_USED_GRANULARITY:
            api_key.last_used_at = now
            await self._session.commit()
        return api_key

    async def create_api_key(
        self,
        *,
        name: str,
        project_id: str,
        scope: str = "read",
        expires_at: datetime | None = None,
    ) -> tuple[ApiKey, str]:
        """Returns (ApiKey ORM, raw_key). raw_key is shown only once."""
        if scope not in VALID_SCOPES:
            raise RegistryError("INVALID_SCOPE", f"scope must be one of {list(VALID_SCOPES)}", status_code=422)
        raw_key = API_KEY_PREFIX + secrets.token_urlsafe(32)
        api_key = await self._repo.create(
            name=name,
            key_hash=_hash_api_key(raw_key),
            project_id=project_id,
            scope=scope,
            expires_at=expires_at,
        )
        await self._session.commit()
        return api_key, raw_key

    async def revoke_api_key(self, api_key_id: uuid.UUID) -> ApiKey:
        key = await self._repo.revoke(api_key_id)
        if key is None:
            raise RegistryError("NOT_FOUND", "API key not found", status_code=404)
        await self._session.commit()
        return key
