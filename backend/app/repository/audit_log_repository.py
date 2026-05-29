from __future__ import annotations

import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.models import EntityAuditLog


class AuditLogRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(
        self,
        *,
        actor: str,
        action: str,
        target_type: str,
        target_id: str,
        before_snapshot: dict | None = None,
        after_snapshot: dict | None = None,
    ) -> EntityAuditLog:
        entry = EntityAuditLog(
            actor=actor,
            action=action,
            target_type=target_type,
            target_id=target_id,
            before_snapshot=before_snapshot,
            after_snapshot=after_snapshot,
        )
        self._session.add(entry)
        await self._session.flush()
        return entry
