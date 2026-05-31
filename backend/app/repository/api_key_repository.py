from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.models import ApiKey, Project, UserAccount


class ApiKeyRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_hash(self, key_hash: str) -> ApiKey | None:
        result = await self._session.execute(
            select(ApiKey).where(ApiKey.key_hash == key_hash, ApiKey.revoked_at.is_(None))
        )
        return result.scalar_one_or_none()

    async def get_by_id(self, api_key_id: uuid.UUID) -> ApiKey | None:
        result = await self._session.execute(select(ApiKey).where(ApiKey.id == api_key_id))
        return result.scalar_one_or_none()

    async def create(
        self,
        *,
        name: str,
        key_hash: str,
        scopes: list[str],
        project_id: uuid.UUID | None = None,
        created_by: uuid.UUID | None = None,
    ) -> ApiKey:
        key = ApiKey(
            name=name,
            key_hash=key_hash,
            scopes=scopes,
            project_id=project_id,
            created_by=created_by,
        )
        self._session.add(key)
        await self._session.flush()
        await self._session.refresh(key)
        return key

    async def list_by_user(
        self, user_id: uuid.UUID
    ) -> list[tuple[ApiKey, str | None, str | None]]:
        """Returns (ApiKey, project_name, owner_role) tuples for user view."""
        stmt = (
            select(ApiKey, Project.alias, UserAccount.role)
            .outerjoin(Project, ApiKey.project_id == Project.id)
            .outerjoin(UserAccount, ApiKey.created_by == UserAccount.id)
            .where(ApiKey.created_by == user_id)
            .order_by(ApiKey.created_at.desc())
        )
        result = await self._session.execute(stmt)
        return [(row[0], row[1], row[2]) for row in result.all()]

    async def list_all(
        self,
        *,
        created_by_email: str | None = None,
        is_active: bool | None = None,
    ) -> list[tuple[ApiKey, str | None, str | None, str | None]]:
        """Returns (ApiKey, owner_email, project_name, owner_role) for admin view."""
        stmt = (
            select(ApiKey, UserAccount.email, Project.alias, UserAccount.role)
            .outerjoin(UserAccount, ApiKey.created_by == UserAccount.id)
            .outerjoin(Project, ApiKey.project_id == Project.id)
            .order_by(ApiKey.created_at.desc())
        )
        if is_active is True:
            stmt = stmt.where(ApiKey.revoked_at.is_(None))
        elif is_active is False:
            stmt = stmt.where(ApiKey.revoked_at.is_not(None))
        if created_by_email:
            stmt = stmt.where(UserAccount.email.ilike(f"%{created_by_email}%"))
        result = await self._session.execute(stmt)
        return [(row[0], row[1], row[2], row[3]) for row in result.all()]

    async def revoke(self, api_key_id: uuid.UUID) -> ApiKey | None:
        key = await self.get_by_id(api_key_id)
        if key is None:
            return None
        key.revoked_at = datetime.now(timezone.utc)
        await self._session.flush()
        await self._session.refresh(key)
        return key
