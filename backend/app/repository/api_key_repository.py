from __future__ import annotations

import uuid
from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.models import ApiKey, Project


class ApiKeyRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_hash(self, key_hash: str) -> ApiKey | None:
        result = await self._session.execute(
            select(ApiKey).where(ApiKey.key_hash == key_hash, ApiKey.revoked_at.is_(None))
        )
        return result.scalar_one_or_none()

    async def get_by_id(self, api_key_id: uuid.UUID) -> ApiKey | None:
        return await self._session.get(ApiKey, api_key_id)

    async def create(self, **fields) -> ApiKey:
        key = ApiKey(**fields)
        self._session.add(key)
        await self._session.flush()
        await self._session.refresh(key)
        return key

    async def list_all(
        self,
        *,
        project_id: str | None = None,
        is_active: bool | None = None,
    ) -> list[tuple[ApiKey, str | None]]:
        """Returns (ApiKey, project_alias) tuples, newest first."""
        stmt = (
            select(ApiKey, Project.alias)
            .outerjoin(Project, ApiKey.project_id == Project.id)
            .order_by(ApiKey.created_at.desc())
        )
        if is_active is True:
            stmt = stmt.where(ApiKey.revoked_at.is_(None))
        elif is_active is False:
            stmt = stmt.where(ApiKey.revoked_at.is_not(None))
        if project_id:
            stmt = stmt.where(ApiKey.project_id == project_id)
        result = await self._session.execute(stmt)
        return [(row[0], row[1]) for row in result.all()]

    async def revoke(self, api_key_id: uuid.UUID) -> ApiKey | None:
        key = await self.get_by_id(api_key_id)
        if key is None:
            return None
        if key.revoked_at is None:
            key.revoked_at = datetime.now(UTC)
            await self._session.flush()
        return key
