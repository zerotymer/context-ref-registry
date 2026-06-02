from __future__ import annotations

import uuid

from sqlalchemy import asc, delete, desc, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.enums import EntityStatus, EntityType
from app.domain.models import Entity, EntityTag
from app.domain.schemas import EntityCreate, EntityUpdate
from app.exceptions import RegistryError


def _apply_visibility(stmt, visible_project_ids: list[str] | None):
    """Apply project visibility filter to a SELECT statement.

    visible_project_ids=None  → admin, no filter
    visible_project_ids=[]    → public only (project_id IS NULL)
    visible_project_ids=[...] → public OR in the given projects
    """
    if visible_project_ids is None:
        return stmt
    if not visible_project_ids:
        return stmt.where(Entity.project_id.is_(None))
    return stmt.where(or_(Entity.project_id.is_(None), Entity.project_id.in_(visible_project_ids)))


class EntityRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(self, data: EntityCreate) -> Entity:
        entity = Entity(
            id=data.id if data.id is not None else uuid.uuid4(),
            type=data.type,
            canonical_name=data.canonical_name,
            description=data.description,
            status=data.status,
            confidence=data.confidence,
            project_id=data.project_id,
        )
        self._session.add(entity)
        await self._session.flush()
        await self._session.refresh(entity)
        return entity

    async def get_by_id(self, entity_id: uuid.UUID) -> Entity | None:
        result = await self._session.execute(
            select(Entity).where(Entity.id == entity_id)
        )
        return result.scalar_one_or_none()

    async def update(self, entity: Entity, data: EntityUpdate) -> Entity:
        for field, value in data.model_dump(exclude_unset=True).items():
            setattr(entity, field, value)
        await self._session.flush()
        await self._session.refresh(entity)
        return entity

    async def list(
        self,
        status: EntityStatus | None = None,
        types: list[EntityType] | None = None,
        tags: list[str] | None = None,
        limit: int = 20,
        offset: int = 0,
        sort: str = "created_at",
        order: str = "desc",
        visible_project_ids: list[str] | None = None,
        project_id: str | None = None,
    ) -> tuple[list[Entity], int]:
        # If project_id is requested but not visible, return empty immediately
        if project_id is not None and visible_project_ids is not None and project_id not in visible_project_ids:
            return [], 0

        count_stmt = _apply_visibility(select(func.count()).select_from(Entity), visible_project_ids)
        if project_id is not None:
            count_stmt = count_stmt.where(Entity.project_id == project_id)
        if status:
            count_stmt = count_stmt.where(Entity.status == status)
        if types:
            count_stmt = count_stmt.where(Entity.type.in_(types))
        if tags:
            for tag in tags:
                sub = select(EntityTag.entity_id).where(EntityTag.tag == tag).scalar_subquery()
                count_stmt = count_stmt.where(Entity.id.in_(sub))
        total = (await self._session.execute(count_stmt)).scalar_one()

        sort_col = {
            "created_at": Entity.created_at,
            "updated_at": Entity.updated_at,
            "canonical_name": Entity.canonical_name,
        }[sort]
        order_fn = desc if order == "desc" else asc
        stmt = _apply_visibility(select(Entity), visible_project_ids)
        if project_id is not None:
            stmt = stmt.where(Entity.project_id == project_id)
        if status:
            stmt = stmt.where(Entity.status == status)
        if types:
            stmt = stmt.where(Entity.type.in_(types))
        if tags:
            for tag in tags:
                sub = select(EntityTag.entity_id).where(EntityTag.tag == tag).scalar_subquery()
                stmt = stmt.where(Entity.id.in_(sub))
        stmt = stmt.order_by(order_fn(sort_col)).limit(limit).offset(offset)
        items = (await self._session.execute(stmt)).scalars().all()

        return list(items), total

    async def replace_tags(self, entity_id: uuid.UUID, tags: list[str]) -> None:
        await self._session.execute(delete(EntityTag).where(EntityTag.entity_id == entity_id))
        for tag in tags:
            self._session.add(EntityTag(entity_id=entity_id, tag=tag))
        if tags:
            await self._session.flush()

    async def add_tag(self, entity_id: uuid.UUID, tag: str) -> EntityTag:
        existing = (
            await self._session.execute(
                select(EntityTag).where(EntityTag.entity_id == entity_id, EntityTag.tag == tag)
            )
        ).scalar_one_or_none()
        if existing is not None:
            raise RegistryError(code="TAG_EXISTS", message=f"Tag '{tag}' already exists on this entity", status_code=409)
        entity_tag = EntityTag(entity_id=entity_id, tag=tag)
        self._session.add(entity_tag)
        await self._session.flush()
        return entity_tag

    async def remove_tag(self, entity_id: uuid.UUID, tag: str) -> None:
        entity_tag = (
            await self._session.execute(
                select(EntityTag).where(EntityTag.entity_id == entity_id, EntityTag.tag == tag)
            )
        ).scalar_one_or_none()
        if entity_tag is None:
            raise RegistryError(code="TAG_NOT_FOUND", message=f"Tag '{tag}' not found on this entity", status_code=404)
        await self._session.delete(entity_tag)
        await self._session.flush()

    async def list_all_tags(self) -> list[tuple[str, int]]:
        stmt = (
            select(EntityTag.tag, func.count().label("count"))
            .group_by(EntityTag.tag)
            .order_by(EntityTag.tag)
        )
        result = await self._session.execute(stmt)
        return list(result.all())

    async def get_by_tag_in_project(
        self,
        project_id: str,
        tag: str,
    ) -> list[Entity]:
        """Return all entities in a project that have the given tag."""
        stmt = (
            select(Entity)
            .join(EntityTag, EntityTag.entity_id == Entity.id)
            .where(Entity.project_id == project_id, EntityTag.tag == tag)
        )
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def search(
        self,
        query: str,
        types: list | None = None,
        tags: list[str] | None = None,
        limit: int = 10,
        visible_project_ids: list[str] | None = None,
    ) -> list[tuple[Entity, str]]:
        from app.domain.models import EntityAlias

        results: list[tuple[Entity, str]] = []
        seen_ids: set[uuid.UUID] = set()

        def _apply_tag_filter(s):
            if tags:
                for tag in tags:
                    sub = select(EntityTag.entity_id).where(EntityTag.tag == tag).scalar_subquery()
                    s = s.where(Entity.id.in_(sub))
            return s

        # 1. alias exact match
        stmt = (
            select(Entity)
            .join(EntityAlias, EntityAlias.entity_id == Entity.id)
            .where(EntityAlias.alias == query, EntityAlias.is_active == True)  # noqa: E712
        )
        stmt = _apply_visibility(stmt, visible_project_ids)
        if types:
            stmt = stmt.where(Entity.type.in_(types))
        stmt = _apply_tag_filter(stmt)
        result = await self._session.execute(stmt.distinct().limit(limit))
        for entity in result.scalars().all():
            if entity.id not in seen_ids:
                seen_ids.add(entity.id)
                results.append((entity, "alias_exact"))

        # 2. canonical_name partial match (ILIKE)
        remaining = limit - len(results)
        if remaining > 0:
            stmt2 = _apply_visibility(
                select(Entity).where(Entity.canonical_name.ilike(f"%{query}%")),
                visible_project_ids,
            )
            if types:
                stmt2 = stmt2.where(Entity.type.in_(types))
            stmt2 = _apply_tag_filter(stmt2)
            result2 = await self._session.execute(stmt2.limit(remaining))
            for entity in result2.scalars().all():
                if entity.id not in seen_ids:
                    seen_ids.add(entity.id)
                    results.append((entity, "canonical_name_partial"))

        return results
