from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from sqlalchemy.dialects.postgresql import insert as pg_insert

from app.domain.models import EntityAlias, EntityContext, EntityMetadata, EntityRelation, EntityTag, SourceRef
from app.domain.schemas import (
    BatchIngestRequest,
    BatchIngestResult,
    IngestCounts,
    IngestEntityInput,
)
from app.exceptions import RegistryError
from app.repository.entity_repository import EntityRepository
from app.repository.history_repository import HistoryRepository
from app.service.entity_service import _entity_to_snapshot


class IngestService:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._entity_repo = EntityRepository(session)
        self._hist_repo = HistoryRepository(session)

    async def batch_ingest(self, req: BatchIngestRequest) -> BatchIngestResult:
        source_ref = await self._upsert_source_ref(req.source)

        created = IngestCounts()
        updated = IngestCounts()
        warnings: list[str] = []

        # Pre-assign UUIDs and build the set for relation validation
        assigned_ids: list[uuid.UUID] = [
            item.id if item.id is not None else uuid.uuid4()
            for item in req.entities
        ]
        batch_entity_ids: set[uuid.UUID] = set(assigned_ids)

        for item, entity_id in zip(req.entities, assigned_ids):
            was_created, entity = await self._upsert_entity(item, entity_id)
            if was_created:
                created.entities += 1
            else:
                updated.entities += 1

            alias_count = await self._upsert_aliases(entity_id, item.aliases)
            created.aliases += alias_count

            ctx_count = await self._add_contexts(entity_id, item.contexts, source_ref.id)
            created.contexts += ctx_count

            if item.metadata:
                await self._upsert_metadata(entity_id, item.metadata)

            if item.tags:
                await self._upsert_tags(entity_id, item.tags)

            rev_no = await self._hist_repo.next_revision_no(entity_id)
            await self._hist_repo.create(
                entity_id=entity_id,
                revision_no=rev_no,
                snapshot=_entity_to_snapshot(entity),
                change_type="create" if was_created else "update",
                changed_by=req.source.name,
            )

        for rel_item in req.relations:
            await self._validate_relation_target(rel_item.from_entity_id, "from_entity_id", batch_entity_ids)
            await self._validate_relation_target(rel_item.to_entity_id, "to_entity_id", batch_entity_ids)

            relation = EntityRelation(
                id=rel_item.id if rel_item.id is not None else uuid.uuid4(),
                from_entity_id=rel_item.from_entity_id,
                to_entity_id=rel_item.to_entity_id,
                relation_type=rel_item.relation_type,
                description=rel_item.description,
                confidence=rel_item.confidence,
            )
            self._session.add(relation)
            await self._session.flush()
            created.relations += 1

        return BatchIngestResult(
            source_ref_id=source_ref.id,
            created=created,
            updated=updated,
            warnings=warnings,
        )

    async def _upsert_entity(self, item: IngestEntityInput, entity_id: uuid.UUID) -> tuple[bool, "Entity"]:
        """Returns (was_created, entity)."""
        from app.domain.models import Entity

        existing = await self._entity_repo.get_by_id(entity_id)
        if existing is None:
            entity = Entity(
                id=entity_id,
                type=item.type,
                canonical_name=item.canonical_name,
                description=item.description,
                status=item.status,
                confidence=item.confidence,
            )
            self._session.add(entity)
            await self._session.flush()
            await self._session.refresh(entity)
            return True, entity

        if existing.type != item.type.value:
            raise RegistryError(
                code="TYPE_CHANGE_FORBIDDEN",
                message=f"Cannot change type of entity {entity_id} from {existing.type} to {item.type}",
                status_code=400,
            )
        existing.canonical_name = item.canonical_name
        if item.description is not None:
            existing.description = item.description
        existing.status = item.status
        existing.confidence = item.confidence
        await self._session.flush()
        return False, existing

    async def _validate_relation_target(
        self,
        target_id: uuid.UUID,
        field: str,
        batch_entity_ids: set[uuid.UUID],
    ) -> None:
        if target_id in batch_entity_ids:
            return
        existing = await self._entity_repo.get_by_id(target_id)
        if existing is None:
            raise RegistryError(
                code="INVALID_RELATION_TARGET",
                message=f"{field} does not exist in existing registry or current batch.",
                status_code=400,
                details={field: str(target_id)},
            )

    async def _upsert_source_ref(self, source) -> SourceRef:
        result = await self._session.execute(
            select(SourceRef).where(SourceRef.uri == source.uri)
        )
        existing = result.scalar_one_or_none()
        if existing is not None:
            if source.version is not None:
                existing.version = source.version
            return existing

        ref = SourceRef(
            uri=source.uri,
            title=source.name,
            version=source.version,
        )
        self._session.add(ref)
        await self._session.flush()
        await self._session.refresh(ref)
        return ref

    async def _upsert_aliases(self, entity_id: uuid.UUID, aliases: dict) -> int:
        count = 0
        for locale, alias_list in aliases.items():
            for alias_text in alias_list:
                result = await self._session.execute(
                    select(EntityAlias).where(
                        EntityAlias.entity_id == entity_id,
                        EntityAlias.locale == locale,
                        EntityAlias.alias == alias_text,
                        EntityAlias.is_active == True,  # noqa: E712
                    )
                )
                if result.scalar_one_or_none() is not None:
                    continue
                self._session.add(
                    EntityAlias(
                        entity_id=entity_id,
                        locale=locale,
                        alias=alias_text,
                        is_primary=False,
                    )
                )
                count += 1
        if count:
            await self._session.flush()
        return count

    async def _add_contexts(self, entity_id: uuid.UUID, contexts: list, source_ref_id: uuid.UUID) -> int:
        for ctx_item in contexts:
            self._session.add(
                EntityContext(
                    entity_id=entity_id,
                    context_type=ctx_item.context_type,
                    title=ctx_item.title,
                    body=ctx_item.body,
                    language=ctx_item.language,
                    source_ref_id=source_ref_id,
                )
            )
        if contexts:
            await self._session.flush()
        return len(contexts)

    async def _upsert_tags(self, entity_id: uuid.UUID, tags: list[str]) -> None:
        """tags 있으면 ON CONFLICT DO NOTHING으로 삽입 (기존 태그 유지)."""
        for tag in tags:
            stmt = (
                pg_insert(EntityTag)
                .values(entity_id=entity_id, tag=tag)
                .on_conflict_do_nothing(constraint="uq_entity_tag")
            )
            await self._session.execute(stmt)
        await self._session.flush()

    async def _upsert_metadata(self, entity_id: uuid.UUID, metadata: dict) -> None:
        result = await self._session.execute(
            select(EntityMetadata).where(EntityMetadata.entity_id == entity_id)
        )
        existing = result.scalar_one_or_none()
        if existing is not None:
            existing.data = metadata
        else:
            self._session.add(
                EntityMetadata(
                    entity_id=entity_id,
                    meta_type="ingest",
                    data=metadata,
                )
            )
        await self._session.flush()
