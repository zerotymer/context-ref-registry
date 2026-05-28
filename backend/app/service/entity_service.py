from __future__ import annotations

import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.enums import EntityStatus, EntityType
from app.domain.models import Entity
from app.domain.schemas import EntityCreate, EntityHistoryListResponse, EntityHistoryRead, EntityUpdate
from app.exceptions import RegistryError
from app.repository.entity_repository import EntityRepository
from app.repository.history_repository import HistoryRepository


def _entity_to_snapshot(entity: Entity) -> dict:
    return {
        "id": str(entity.id),
        "type": entity.type.value if hasattr(entity.type, "value") else entity.type,
        "canonical_name": entity.canonical_name,
        "description": entity.description,
        "status": entity.status.value if hasattr(entity.status, "value") else entity.status,
        "confidence": entity.confidence,
        "replacement_entity_id": str(entity.replacement_entity_id) if entity.replacement_entity_id else None,
        "deprecation_reason": entity.deprecation_reason,
    }


class EntityService:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._repo = EntityRepository(session)
        self._hist_repo = HistoryRepository(session)

    async def list(
        self,
        status: EntityStatus | None,
        types: list[EntityType] | None,
        tags: list[str] | None,
        limit: int,
        offset: int,
        sort: str,
        order: str,
    ) -> tuple[list[Entity], int]:
        return await self._repo.list(status, types, tags, limit, offset, sort, order)

    async def create(self, data: EntityCreate, changed_by: str | None = None) -> Entity:
        entity = await self._repo.create(data)
        if data.tags:
            await self._repo.replace_tags(entity.id, data.tags)
            await self._session.refresh(entity)
        rev_no = await self._hist_repo.next_revision_no(entity.id)
        await self._hist_repo.create(
            entity_id=entity.id,
            revision_no=rev_no,
            snapshot=_entity_to_snapshot(entity),
            change_type="create",
            changed_by=changed_by,
        )
        return entity

    async def get_by_id(self, entity_id: uuid.UUID) -> Entity:
        entity = await self._repo.get_by_id(entity_id)
        if entity is None:
            raise RegistryError(
                code="ENTITY_NOT_FOUND",
                message=f"Entity {entity_id} not found",
                status_code=404,
            )
        return entity

    async def update(
        self, entity_id: uuid.UUID, data: EntityUpdate, changed_by: str | None = None
    ) -> Entity:
        entity = await self.get_by_id(entity_id)
        before_snapshot = _entity_to_snapshot(entity)

        entity_fields = {
            k: v
            for k, v in data.model_dump(exclude_unset=True).items()
            if k not in {"tags", "change_reason"}
        }
        if entity_fields:
            await self._repo.update(entity, EntityUpdate(**entity_fields))
        if data.tags is not None:
            await self._repo.replace_tags(entity_id, data.tags)
            await self._session.refresh(entity)

        after_snapshot = _entity_to_snapshot(entity)
        changed_fields: dict | None = {
            k: {"before": before_snapshot[k], "after": after_snapshot[k]}
            for k in before_snapshot
            if before_snapshot[k] != after_snapshot[k]
        } or None

        change_type = "update"
        if changed_fields and "status" in changed_fields:
            new_status = changed_fields["status"]["after"]
            change_type = "deprecate" if new_status == "deprecated" else "status_change"

        rev_no = await self._hist_repo.next_revision_no(entity_id)
        await self._hist_repo.create(
            entity_id=entity_id,
            revision_no=rev_no,
            snapshot=before_snapshot,
            change_type=change_type,
            changed_fields=changed_fields,
            change_reason=data.change_reason,
            changed_by=changed_by,
        )

        return entity

    async def add_tag(self, entity_id: uuid.UUID, tag: str) -> Entity:
        entity = await self.get_by_id(entity_id)
        await self._repo.add_tag(entity_id, tag)
        await self._session.refresh(entity)
        return entity

    async def remove_tag(self, entity_id: uuid.UUID, tag: str) -> None:
        await self.get_by_id(entity_id)
        await self._repo.remove_tag(entity_id, tag)

    async def list_all_tags(self) -> list[tuple[str, int]]:
        return await self._repo.list_all_tags()

    async def list_history(
        self, entity_id: uuid.UUID, limit: int = 50, offset: int = 0
    ) -> tuple[list, int]:
        await self.get_by_id(entity_id)
        return await self._hist_repo.list_by_entity(entity_id, limit, offset)

    async def get_history_revision(self, entity_id: uuid.UUID, revision_no: int):
        await self.get_by_id(entity_id)
        history = await self._hist_repo.get_by_revision(entity_id, revision_no)
        if history is None:
            raise RegistryError(
                code="REVISION_NOT_FOUND",
                message=f"Revision {revision_no} not found for entity {entity_id}",
                status_code=404,
            )
        return history
