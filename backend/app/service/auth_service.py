from __future__ import annotations

import hashlib
import secrets
import uuid
from datetime import datetime, timedelta, timezone

import jwt
from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import (
    BOOTSTRAP_ADMIN_DISPLAY_NAME,
    BOOTSTRAP_ADMIN_LOGIN_ID,
    BOOTSTRAP_ADMIN_PASSWORD,
    JWT_ALGORITHM,
    JWT_EXPIRE_MINUTES,
    JWT_SECRET,
)
from app.domain.models import ApiKey, UserAccount
from app.exceptions import RegistryError
from app.repository.api_key_repository import ApiKeyRepository
from app.repository.user_repository import UserRepository

_ph = PasswordHasher()


def hash_password(plain: str) -> str:
    return _ph.hash(plain)


def verify_password(plain: str, hashed: str) -> bool:
    try:
        return _ph.verify(hashed, plain)
    except VerifyMismatchError:
        return False


def _normalize_login_id(login_id: str) -> str:
    return login_id.strip().lower()


def create_access_token(user_id: uuid.UUID) -> str:
    expire = datetime.now(timezone.utc) + timedelta(minutes=JWT_EXPIRE_MINUTES)
    payload = {"sub": str(user_id), "exp": expire}
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)


def decode_access_token(token: str) -> uuid.UUID:
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        return uuid.UUID(payload["sub"])
    except Exception:
        raise RegistryError("UNAUTHORIZED", "Invalid or expired token", status_code=401)


def _hash_api_key(raw_key: str) -> str:
    return hashlib.sha256(raw_key.encode()).hexdigest()


_VALID_ROLES = {"admin", "project_admin", "user"}


class AuthService:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._user_repo = UserRepository(session)
        self._api_key_repo = ApiKeyRepository(session)

    async def login(self, login_id: str, password: str) -> tuple[UserAccount, str]:
        norm_id = _normalize_login_id(login_id)
        user = await self._user_repo.get_by_login_id(norm_id)
        if user is None or not verify_password(password, user.password_hash):
            raise RegistryError("UNAUTHORIZED", "Invalid credentials", status_code=401)
        if not user.is_active:
            raise RegistryError("UNAUTHORIZED", "Account is inactive", status_code=401)
        token = create_access_token(user.id)
        return user, token

    async def get_user_by_token(self, token: str) -> UserAccount:
        user_id = decode_access_token(token)
        user = await self._user_repo.get_by_id(user_id)
        if user is None or not user.is_active:
            raise RegistryError("UNAUTHORIZED", "User not found or inactive", status_code=401)
        return user

    async def get_user_by_api_key(self, raw_key: str) -> tuple[UserAccount | None, ApiKey]:
        key_hash = _hash_api_key(raw_key)
        api_key = await self._api_key_repo.get_by_hash(key_hash)
        if api_key is None:
            raise RegistryError("UNAUTHORIZED", "Invalid or revoked API key", status_code=401)
        user: UserAccount | None = None
        if api_key.created_by is not None:
            user = await self._user_repo.get_by_id(api_key.created_by)
        return user, api_key

    async def create_user(
        self,
        *,
        login_id: str,
        password: str,
        display_name: str,
        role: str = "user",
        must_change_password: bool = False,
        created_by: uuid.UUID | None = None,
    ) -> UserAccount:
        norm_id = _normalize_login_id(login_id)
        existing = await self._user_repo.get_by_login_id(norm_id)
        if existing is not None:
            raise RegistryError("CONFLICT", "Login ID already registered", status_code=409)
        pw_hash = hash_password(password)
        user = await self._user_repo.create(
            login_id=norm_id,
            password_hash=pw_hash,
            display_name=display_name,
            role=role,
            must_change_password=must_change_password,
            created_by=created_by,
        )
        await self._session.commit()
        return user

    async def change_password(
        self,
        user_id: uuid.UUID,
        current_password: str,
        new_password: str,
    ) -> None:
        """Verify current password, update to new, and hard-delete all API keys."""
        user = await self._user_repo.get_by_id(user_id)
        if user is None:
            raise RegistryError("NOT_FOUND", "User not found", status_code=404)
        if not verify_password(current_password, user.password_hash):
            raise RegistryError("UNAUTHORIZED", "Current password is incorrect", status_code=401)
        pw_hash = hash_password(new_password)
        await self._user_repo.update(user, password_hash=pw_hash, must_change_password=False)
        await self._api_key_repo.delete_all_by_user(user_id)
        await self._session.commit()

    async def create_api_key(
        self,
        *,
        name: str,
        scopes: list[str],
        project_id: uuid.UUID | None = None,
        created_by: uuid.UUID | None = None,
    ) -> tuple[ApiKey, str]:
        """Returns (ApiKey ORM, raw_key). raw_key shown only once."""
        raw_key = secrets.token_urlsafe(32)
        key_hash = _hash_api_key(raw_key)
        api_key = await self._api_key_repo.create(
            name=name,
            key_hash=key_hash,
            scopes=scopes,
            project_id=project_id,
            created_by=created_by,
        )
        await self._session.commit()
        return api_key, raw_key

    async def list_api_keys(
        self, user_id: uuid.UUID
    ) -> list[tuple[ApiKey, str | None, str | None]]:
        """Returns (ApiKey, project_name, owner_role) tuples."""
        return await self._api_key_repo.list_by_user(user_id)

    async def list_all_api_keys(
        self,
        *,
        created_by_login_id: str | None = None,
        is_active: bool | None = None,
    ) -> list[tuple[ApiKey, str | None, str | None, str | None]]:
        """Returns (ApiKey, owner_login_id, project_name, owner_role) tuples."""
        return await self._api_key_repo.list_all(
            created_by_login_id=created_by_login_id,
            is_active=is_active,
        )

    async def revoke_api_key(
        self,
        api_key_id: uuid.UUID,
        *,
        actor_id: uuid.UUID,
        is_admin: bool = False,
    ) -> ApiKey:
        key = await self._api_key_repo.get_by_id(api_key_id)
        if key is None:
            raise RegistryError("NOT_FOUND", "API key not found", status_code=404)
        if not is_admin and key.created_by != actor_id:
            raise RegistryError("FORBIDDEN", "Cannot revoke another user's API key", status_code=403)
        revoked = await self._api_key_repo.revoke(api_key_id)
        await self._session.commit()
        return revoked

    async def list_users(
        self,
        *,
        role: str | None = None,
        is_active: bool | None = None,
        search: str | None = None,
    ) -> list[UserAccount]:
        return await self._user_repo.list_all(role=role, is_active=is_active, search=search)

    async def update_user(
        self,
        user_id: uuid.UUID,
        *,
        display_name: str | None = None,
        role: str | None = None,
        is_active: bool | None = None,
    ) -> UserAccount:
        user = await self._user_repo.get_by_id(user_id)
        if user is None:
            raise RegistryError("NOT_FOUND", "User not found", status_code=404)
        if role is not None and role not in _VALID_ROLES:
            raise RegistryError("INVALID_ROLE", f"Role must be one of {sorted(_VALID_ROLES)}", status_code=422)
        updated = await self._user_repo.update(
            user,
            display_name=display_name,
            role=role,
            is_active=is_active,
        )
        await self._session.commit()
        return updated

    async def reset_password(self, user_id: uuid.UUID, new_password: str) -> None:
        """Admin password reset — updates password and hard-deletes all API keys."""
        user = await self._user_repo.get_by_id(user_id)
        if user is None:
            raise RegistryError("NOT_FOUND", "User not found", status_code=404)
        pw_hash = hash_password(new_password)
        await self._user_repo.update(user, password_hash=pw_hash, must_change_password=True)
        await self._api_key_repo.delete_all_by_user(user_id)
        await self._session.commit()

    async def bootstrap_admin(self) -> None:
        """Create initial admin account if no admin exists."""
        if await self._user_repo.exists_admin():
            return
        norm_id = _normalize_login_id(BOOTSTRAP_ADMIN_LOGIN_ID)
        existing = await self._user_repo.get_by_login_id(norm_id)
        if existing is not None:
            return
        pw_hash = hash_password(BOOTSTRAP_ADMIN_PASSWORD)
        await self._user_repo.create(
            login_id=norm_id,
            password_hash=pw_hash,
            display_name=BOOTSTRAP_ADMIN_DISPLAY_NAME,
            role="admin",
            must_change_password=True,
        )
        await self._session.commit()
