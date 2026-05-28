from __future__ import annotations

import uuid

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.models import EntityHistory


class HistoryRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def next_revision_no(self, entity_id: uuid.UUID) -> int:
        stmt = (
            select(func.coalesce(func.max(EntityHistory.revision_no), 0) + 1)
            .where(EntityHistory.entity_id == entity_id)
        )
        return (await self._session.execute(stmt)).scalar_one()

    async def create(
        self,
        entity_id: uuid.UUID,
        revision_no: int,
        snapshot: dict,
        change_type: str,
        changed_fields: dict | None = None,
        change_reason: str | None = None,
        changed_by: str | None = None,
    ) -> EntityHistory:
        history = EntityHistory(
            entity_id=entity_id,
            revision_no=revision_no,
            snapshot=snapshot,
            changed_fields=changed_fields,
            change_type=change_type,
            change_reason=change_reason,
            changed_by=changed_by,
        )
        self._session.add(history)
        await self._session.flush()
        return history

    async def list_by_entity(
        self, entity_id: uuid.UUID, limit: int = 50, offset: int = 0
    ) -> tuple[list[EntityHistory], int]:
        count = (
            await self._session.execute(
                select(func.count()).select_from(EntityHistory).where(EntityHistory.entity_id == entity_id)
            )
        ).scalar_one()
        items = (
            await self._session.execute(
                select(EntityHistory)
                .where(EntityHistory.entity_id == entity_id)
                .order_by(EntityHistory.revision_no.desc())
                .limit(limit)
                .offset(offset)
            )
        ).scalars().all()
        return list(items), count

    async def get_by_revision(self, entity_id: uuid.UUID, revision_no: int) -> EntityHistory | None:
        return (
            await self._session.execute(
                select(EntityHistory).where(
                    EntityHistory.entity_id == entity_id,
                    EntityHistory.revision_no == revision_no,
                )
            )
        ).scalar_one_or_none()
