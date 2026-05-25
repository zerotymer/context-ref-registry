from __future__ import annotations

import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.enums import ContextType, EntityStatus
from app.domain.models import Entity, EntityContext, EntityRelation
from app.domain.schemas import (
    BundleContextRead,
    BundleEntityRead,
    BundleRelationRead,
    ContextBundleRequest,
    ContextBundleResponse,
    DeprecatedWarning,
)
from app.exceptions import RegistryError
from app.repository.context_repository import ContextRepository
from app.repository.entity_repository import EntityRepository
from app.repository.relation_repository import RelationRepository

_CONTEXT_PRIORITY: list[ContextType] = [
    ContextType.SUMMARY,
    ContextType.BUSINESS_RULE,
    ContextType.VALIDATION_RULE,
    ContextType.IMPLEMENTATION_HINT,
    ContextType.SECURITY_NOTE,
    ContextType.INFRA_NOTE,
    ContextType.DETAILS,
    ContextType.COMPATIBILITY_NOTE,
    ContextType.EXCEPTION_CASE,
]


class BundleService:
    def __init__(self, session: AsyncSession) -> None:
        self._entity_repo = EntityRepository(session)
        self._context_repo = ContextRepository(session)
        self._relation_repo = RelationRepository(session)

    async def get_context_bundle(self, req: ContextBundleRequest) -> ContextBundleResponse:
        root_entities: list[Entity] = []
        for rid in req.root_ids:
            entity = await self._entity_repo.get_by_id(rid)
            if entity is None:
                raise RegistryError(
                    code="ENTITY_NOT_FOUND",
                    message=f"Entity {rid} not found",
                    status_code=404,
                )
            root_entities.append(entity)

        all_entities, all_relations = await self._bfs(root_entities, req)

        root_ids_set = set(req.root_ids)
        roots = [e for e in all_entities if e.id in root_ids_set]
        related = [e for e in all_entities if e.id not in root_ids_set]

        all_contexts: list[EntityContext] = []
        for entity in all_entities:
            ctxs = await self._context_repo.list_by_entity(entity.id, language=req.language)
            all_contexts.extend(ctxs)

        filtered_contexts = _apply_token_budget(all_contexts, req.token_budget)

        warnings: list[DeprecatedWarning] = []
        for entity in all_entities:
            if entity.status == EntityStatus.DEPRECATED:
                warnings.append(
                    DeprecatedWarning(
                        entity_id=entity.id,
                        message="This entity is deprecated.",
                        replacement_entity_id=entity.replacement_entity_id,
                    )
                )

        return ContextBundleResponse(
            roots=[_to_bundle_entity(e) for e in roots],
            entities=[_to_bundle_entity(e) for e in related],
            contexts=[_to_bundle_context(c) for c in filtered_contexts],
            relations=[_to_bundle_relation(r) for r in all_relations],
            warnings=warnings,
        )

    async def _bfs(
        self,
        root_entities: list[Entity],
        req: ContextBundleRequest,
    ) -> tuple[list[Entity], list[EntityRelation]]:
        visited_ids: set[uuid.UUID] = {e.id for e in root_entities}
        entity_map: dict[uuid.UUID, Entity] = {e.id: e for e in root_entities}
        all_relations: list[EntityRelation] = []
        seen_relation_ids: set[uuid.UUID] = set()

        frontier: list[tuple[uuid.UUID, int]] = [(e.id, 0) for e in root_entities]

        while frontier:
            next_frontier: list[tuple[uuid.UUID, int]] = []
            for entity_id, depth in frontier:
                if depth >= req.max_depth:
                    continue
                rels = await self._relation_repo.get_direct_relations(
                    entity_id, req.include_relations
                )
                for rel in rels:
                    if rel.id not in seen_relation_ids:
                        seen_relation_ids.add(rel.id)
                        all_relations.append(rel)

                    neighbor_id = (
                        rel.to_entity_id
                        if rel.from_entity_id == entity_id
                        else rel.from_entity_id
                    )
                    if neighbor_id in visited_ids:
                        continue

                    neighbor = await self._entity_repo.get_by_id(neighbor_id)
                    if neighbor is None:
                        continue
                    if req.include_types and neighbor.type not in req.include_types:
                        continue

                    visited_ids.add(neighbor_id)
                    entity_map[neighbor_id] = neighbor
                    next_frontier.append((neighbor_id, depth + 1))
            frontier = next_frontier

        return list(entity_map.values()), all_relations


def _apply_token_budget(
    contexts: list[EntityContext], token_budget: int
) -> list[EntityContext]:
    priority_map = {ct: i for i, ct in enumerate(_CONTEXT_PRIORITY)}
    sorted_ctxs = sorted(
        contexts, key=lambda c: priority_map.get(c.context_type, len(_CONTEXT_PRIORITY))
    )
    used = 0
    result: list[EntityContext] = []
    for ctx in sorted_ctxs:
        tokens = max(1, len(ctx.body) // 4)
        if used + tokens > token_budget:
            break
        result.append(ctx)
        used += tokens
    return result


def _to_bundle_entity(e: Entity) -> BundleEntityRead:
    return BundleEntityRead(id=e.id, type=e.type, canonical_name=e.canonical_name, status=e.status)


def _to_bundle_context(c: EntityContext) -> BundleContextRead:
    return BundleContextRead(entity_id=c.entity_id, context_type=c.context_type, body=c.body)


def _to_bundle_relation(r: EntityRelation) -> BundleRelationRead:
    return BundleRelationRead(
        from_entity_id=r.from_entity_id,
        to_entity_id=r.to_entity_id,
        relation_type=r.relation_type,
    )
