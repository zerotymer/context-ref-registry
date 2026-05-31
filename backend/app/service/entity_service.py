from __future__ import annotations

import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.enums import EntityStatus, EntityType
from app.domain.models import Entity
from app.domain.schemas import BatchCreateItem, EntityBatchCreateResult, EntityCreate, EntityHistoryListResponse, EntityHistoryRead, EntityUpdate, RevisionCompareResponse, RevisionDiffField
from app.exceptions import RegistryError
from app.repository.entity_repository import EntityRepository
from app.repository.history_repository import HistoryRepository
from app.service.audit_service import AuditService


def _effective_state(history) -> dict:
    """Compute entity state AFTER the revision was applied.

    Snapshot stores the before-image for updates; apply changed_fields["after"]
    to get the actual post-revision state.
    """
    state = dict(history.snapshot)
    if history.changed_fields:
        for field, diff in history.changed_fields.items():
            state[field] = diff["after"]
    return state


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
        self._audit = AuditService(session)

    async def list(
        self,
        status: EntityStatus | None,
        types: list[EntityType] | None,
        tags: list[str] | None,
        limit: int,
        offset: int,
        sort: str,
        order: str,
        visible_project_ids: list[str] | None = None,
    ) -> tuple[list[Entity], int]:
        return await self._repo.list(status, types, tags, limit, offset, sort, order, visible_project_ids)

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
        await self._audit.log(
            actor=changed_by or "system",
            action="entity_create",
            target_type="entity",
            target_id=str(entity.id),
            after_snapshot=_entity_to_snapshot(entity),
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
        audit_action = (
            "entity_status_change" if changed_fields and "status" in changed_fields else "entity_update"
        )
        await self._audit.log(
            actor=changed_by or "system",
            action=audit_action,
            target_type="entity",
            target_id=str(entity_id),
            before_snapshot=before_snapshot,
            after_snapshot=_entity_to_snapshot(entity),
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

    async def resolve_ref(self, ref: str) -> Entity:
        """Resolve any reference pattern (UUID / PROJECT_ID@UUID / PROJECT_ID@TAG) to a single Entity.

        Raises:
            RegistryError("INVALID_REF_FORMAT")    — parse_ref() 실패
            RegistryError("ENTITY_NOT_FOUND")       — 존재하지 않음
            RegistryError("PROJECT_SCOPE_MISMATCH") — SCOPED_UUID: 프로젝트 불일치
            RegistryError("AMBIGUOUS_TAG_REF")      — SCOPED_TAG: 복수 매칭
        """
        from app.domain.ref_pattern import RefKind, parse_ref

        try:
            parsed = parse_ref(ref)
        except ValueError as e:
            raise RegistryError("INVALID_REF_FORMAT", str(e), 422)

        if parsed.kind == RefKind.UUID:
            return await self.get_by_id(uuid.UUID(parsed.identifier))

        if parsed.kind == RefKind.SCOPED_UUID:
            entity = await self.get_by_id(uuid.UUID(parsed.identifier))
            if entity.project_id != parsed.project_id:
                raise RegistryError(
                    "PROJECT_SCOPE_MISMATCH",
                    f"Entity {parsed.identifier} does not belong to project {parsed.project_id!r}",
                    404,
                )
            return entity

        # SCOPED_TAG
        matches = await self._repo.get_by_tag_in_project(parsed.project_id, parsed.identifier)
        if not matches:
            raise RegistryError(
                "ENTITY_NOT_FOUND",
                f"No entity with tag {parsed.identifier!r} in project {parsed.project_id!r}",
                404,
            )
        if len(matches) > 1:
            raise RegistryError(
                "AMBIGUOUS_TAG_REF",
                f"Tag {parsed.identifier!r} matches {len(matches)} entities in project {parsed.project_id!r}",
                422,
                details={"matched_ids": [str(e.id) for e in matches]},
            )
        return matches[0]

    async def batch_create(
        self,
        items: list[EntityCreate],
        changed_by: str,
    ) -> list[BatchCreateItem]:
        """Create multiple entities. Returns per-item success/error (partial success allowed)."""
        results: list[BatchCreateItem] = []
        for idx, item in enumerate(items):
            try:
                entity = await self.create(item, changed_by=changed_by)
                results.append(BatchCreateItem(index=idx, id=str(entity.id), ok=True))
            except Exception as exc:
                await self._session.rollback()
                code = getattr(exc, "code", "UNKNOWN_ERROR")
                message = getattr(exc, "message", str(exc))
                results.append(BatchCreateItem(index=idx, ok=False, error_code=code, error_message=message))
        return results

    async def compare_revisions(
        self, entity_id: uuid.UUID, rev_a_no: int, rev_b_no: int
    ) -> RevisionCompareResponse:
        rev_a = await self.get_history_revision(entity_id, rev_a_no)
        rev_b = await self.get_history_revision(entity_id, rev_b_no)

        state_a = _effective_state(rev_a)
        state_b = _effective_state(rev_b)

        all_keys = set(state_a.keys()) | set(state_b.keys())
        diff = {
            key: RevisionDiffField(
                before=state_a.get(key),
                after=state_b.get(key),
                changed=state_a.get(key) != state_b.get(key),
            )
            for key in sorted(all_keys)
        }
        return RevisionCompareResponse(
            entity_id=entity_id,
            rev_a=EntityHistoryRead.model_validate(rev_a),
            rev_b=EntityHistoryRead.model_validate(rev_b),
            diff=diff,
        )
