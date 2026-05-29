from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.models import ApiKey


class ApiKeyRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_hash(self, key_hash: str) -> ApiKey | None:
        result = await self._session.execute(
            select(ApiKey).where(ApiKey.key_hash == key_hash, ApiKey.revoked_at.is_(None))
        )
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
