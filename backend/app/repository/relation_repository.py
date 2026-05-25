from __future__ import annotations

import uuid
from collections import deque

from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.enums import RelationType
from app.domain.models import EntityRelation
from app.domain.schemas import RelationCreate


class RelationRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def add(self, data: RelationCreate) -> EntityRelation:
        relation = EntityRelation(
            from_entity_id=data.from_entity_id,
            to_entity_id=data.to_entity_id,
            relation_type=data.relation_type,
            description=data.description,
            confidence=data.confidence,
        )
        self._session.add(relation)
        await self._session.flush()
        await self._session.refresh(relation)
        return relation

    async def list_by_entity(
        self,
        entity_id: uuid.UUID,
        direction: str = "both",
        relation_type: RelationType | None = None,
        max_depth: int = 1,
    ) -> list[EntityRelation]:
        visited: set[uuid.UUID] = {entity_id}
        queue: deque[tuple[uuid.UUID, int]] = deque([(entity_id, 0)])
        results: list[EntityRelation] = []
        seen_ids: set[uuid.UUID] = set()

        while queue:
            current_id, depth = queue.popleft()
            if depth >= max_depth:
                continue

            rels = await self._fetch_direct(current_id, direction, relation_type)
            for rel in rels:
                if rel.id not in seen_ids:
                    seen_ids.add(rel.id)
                    results.append(rel)

                next_id = self._next_entity(rel, current_id, direction)
                if next_id is not None and next_id not in visited:
                    visited.add(next_id)
                    queue.append((next_id, depth + 1))

        return results

    async def _fetch_direct(
        self,
        entity_id: uuid.UUID,
        direction: str,
        relation_type: RelationType | None,
    ) -> list[EntityRelation]:
        if direction == "out":
            stmt = select(EntityRelation).where(EntityRelation.from_entity_id == entity_id)
        elif direction == "in":
            stmt = select(EntityRelation).where(EntityRelation.to_entity_id == entity_id)
        else:
            stmt = select(EntityRelation).where(
                or_(
                    EntityRelation.from_entity_id == entity_id,
                    EntityRelation.to_entity_id == entity_id,
                )
            )
        if relation_type is not None:
            stmt = stmt.where(EntityRelation.relation_type == relation_type)
        stmt = stmt.order_by(EntityRelation.created_at)
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    @staticmethod
    def _next_entity(rel: EntityRelation, current_id: uuid.UUID, direction: str) -> uuid.UUID | None:
        if direction == "out":
            return rel.to_entity_id
        if direction == "in":
            return rel.from_entity_id
        # both: follow whichever end is not current
        if rel.from_entity_id == current_id:
            return rel.to_entity_id
        return rel.from_entity_id
