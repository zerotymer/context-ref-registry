from __future__ import annotations

import uuid
from typing import Any

from app.db.session import async_session_factory
from app.domain.enums import EntityType, Locale, RelationType
from app.domain.schemas import ContextBundleRequest
from app.exceptions import RegistryError
from app.mcp.server import mcp
from app.repository.alias_repository import AliasRepository
from app.repository.entity_repository import EntityRepository
from app.repository.relation_repository import RelationRepository
from app.service.alias_service import AliasService
from app.service.bundle_service import BundleService
from app.service.entity_service import EntityService
from app.service.relation_service import RelationService
from app.service.validate_service import ValidateService


def _entity_summary(entity: Any) -> dict:
    return {
        "id": str(entity.id),
        "type": entity.type.value if hasattr(entity.type, "value") else entity.type,
        "canonical_name": entity.canonical_name,
        "status": entity.status.value if hasattr(entity.status, "value") else entity.status,
    }


# ---------------------------------------------------------------------------
# resolve_alias
# ---------------------------------------------------------------------------


@mcp.tool(
    description=(
        "Resolve a mutable alias to its immutable entity ID(s). "
        "Returns status: resolved | ambiguous | not_found. "
        "When ambiguous, ask the user to choose — never pick arbitrarily."
    )
)
async def resolve_alias(
    alias: str,
    locale: str | None = None,
    type: str | None = None,
) -> dict:
    locale_enum = Locale(locale) if locale else None
    type_enum = EntityType(type) if type else None

    async with async_session_factory() as session:
        service = AliasService(session)
        result = await service.resolve(alias, locale_enum, type_enum)

    if result.result == "not_found":
        return {"status": "not_found"}

    if result.result == "resolved" and result.entity:
        return {
            "status": "resolved",
            "entity": {
                "id": str(result.entity.id),
                "type": result.entity.type.value,
                "canonical_name": result.entity.canonical_name,
            },
        }

    # ambiguous
    candidates = []
    if result.candidates:
        for e in result.candidates:
            candidates.append({
                "id": str(e.id),
                "type": e.type.value,
                "canonical_name": e.canonical_name,
                "status": e.status.value,
            })
    return {
        "status": "ambiguous",
        "candidates": candidates,
        "required_action": "ask_user_to_choose_entity_id",
    }


# ---------------------------------------------------------------------------
# get_entity
# ---------------------------------------------------------------------------


@mcp.tool(
    description="Retrieve a single entity by UUID, including its aliases grouped by locale and any deprecation warnings."
)
async def get_entity(id: str) -> dict:
    entity_id = uuid.UUID(id)

    async with async_session_factory() as session:
        service = EntityService(session)
        alias_repo = AliasRepository(session)

        try:
            entity = await service.get_by_id(entity_id)
        except RegistryError as exc:
            return {"error": exc.code, "message": exc.message}

        alias_rows = await alias_repo.list_by_entity(entity_id)

    aliases_by_locale: dict[str, list[str]] = {}
    for a in alias_rows:
        locale_val = a.locale.value if hasattr(a.locale, "value") else a.locale
        aliases_by_locale.setdefault(locale_val, []).append(a.alias)

    status_val = entity.status.value if hasattr(entity.status, "value") else entity.status
    type_val = entity.type.value if hasattr(entity.type, "value") else entity.type

    warnings = []
    if status_val == "deprecated":
        w: dict[str, Any] = {
            "type": "deprecated_entity",
            "message": "This entity is deprecated.",
        }
        if entity.replacement_entity_id:
            w["replacement_entity_id"] = str(entity.replacement_entity_id)
        warnings.append(w)

    tags = [t.tag for t in entity.tags] if entity.tags else []

    return {
        "entity": {
            "id": str(entity.id),
            "type": type_val,
            "canonical_name": entity.canonical_name,
            "description": entity.description,
            "status": status_val,
            "confidence": entity.confidence,
            "tags": tags,
            "replacement_entity_id": (
                str(entity.replacement_entity_id) if entity.replacement_entity_id else None
            ),
        },
        "aliases": aliases_by_locale,
        "warnings": warnings,
    }


# ---------------------------------------------------------------------------
# search_entities
# ---------------------------------------------------------------------------


@mcp.tool(
    description=(
        "Search for entities by keyword. Searches alias (exact) then canonical_name (partial). "
        "Optionally filter by entity types or tags (AND logic)."
    )
)
async def search_entities(
    query: str,
    types: list[str] | None = None,
    tags: list[str] | None = None,
    limit: int = 10,
) -> dict:
    type_enums = [EntityType(t) for t in types] if types else None

    async with async_session_factory() as session:
        repo = EntityRepository(session)
        hits = await repo.search(query, type_enums, tags, limit)

    results = []
    for entity, match_reason in hits:
        score = 1.0 if match_reason == "alias_exact" else 0.7
        results.append({
            **_entity_summary(entity),
            "score": score,
            "match_reason": match_reason,
        })

    return {"results": results}


# ---------------------------------------------------------------------------
# get_related_entities
# ---------------------------------------------------------------------------


@mcp.tool(
    description="Retrieve entities related to a given entity via the relation graph."
)
async def get_related_entities(
    id: str,
    direction: str = "both",
    relation_types: list[str] | None = None,
    max_depth: int = 1,
) -> dict:
    entity_id = uuid.UUID(id)
    rel_type_enums = [RelationType(r) for r in relation_types] if relation_types else None

    async with async_session_factory() as session:
        service = RelationService(session)
        entity_repo = EntityRepository(session)

        try:
            relations = await service.list_relations(
                entity_id,
                direction=direction,
                relation_type=rel_type_enums[0] if rel_type_enums and len(rel_type_enums) == 1 else None,
                max_depth=max_depth,
            )
        except RegistryError as exc:
            return {"error": exc.code, "message": exc.message}

        # Collect neighbor IDs
        neighbor_ids: set[uuid.UUID] = set()
        for rel in relations:
            if rel.from_entity_id != entity_id:
                neighbor_ids.add(rel.from_entity_id)
            if rel.to_entity_id != entity_id:
                neighbor_ids.add(rel.to_entity_id)

        entities = []
        for nid in neighbor_ids:
            e = await entity_repo.get_by_id(nid)
            if e:
                entities.append(_entity_summary(e))

    rel_list = [
        {
            "from_entity_id": str(r.from_entity_id),
            "to_entity_id": str(r.to_entity_id),
            "relation_type": r.relation_type.value if hasattr(r.relation_type, "value") else r.relation_type,
        }
        for r in relations
        # filter by relation_types if multiple types requested
        if (not rel_type_enums or r.relation_type in rel_type_enums)
    ]

    return {
        "root_id": str(entity_id),
        "relations": rel_list,
        "entities": entities,
    }


# ---------------------------------------------------------------------------
# get_context_bundle
# ---------------------------------------------------------------------------


@mcp.tool(
    description=(
        "The primary tool for retrieving rich context about one or more entities. "
        "Returns roots, related entities, contexts, relations, and deprecation warnings. "
        "Use max_depth and token_budget to control scope."
    )
)
async def get_context_bundle(
    root_ids: list[str],
    max_depth: int = 2,
    token_budget: int = 8000,
    include_types: list[str] | None = None,
    include_relations: list[str] | None = None,
    language: str = "ko",
) -> dict:
    root_uuid_list = [uuid.UUID(r) for r in root_ids]
    type_enums = [EntityType(t) for t in include_types] if include_types else None
    rel_enums = [RelationType(r) for r in include_relations] if include_relations else None
    locale_enum = Locale(language)

    req = ContextBundleRequest(
        root_ids=root_uuid_list,
        max_depth=max_depth,
        token_budget=token_budget,
        include_types=type_enums,
        include_relations=rel_enums,
        language=locale_enum,
    )

    async with async_session_factory() as session:
        service = BundleService(session)
        try:
            bundle = await service.get_context_bundle(req)
        except RegistryError as exc:
            return {"error": exc.code, "message": exc.message}

    def _ser_entity(e: Any) -> dict:
        return {
            "id": str(e.id),
            "type": e.type.value if hasattr(e.type, "value") else e.type,
            "canonical_name": e.canonical_name,
            "status": e.status.value if hasattr(e.status, "value") else e.status,
        }

    def _ser_context(c: Any) -> dict:
        return {
            "entity_id": str(c.entity_id),
            "context_type": c.context_type.value if hasattr(c.context_type, "value") else c.context_type,
            "body": c.body,
        }

    def _ser_relation(r: Any) -> dict:
        return {
            "from_entity_id": str(r.from_entity_id),
            "to_entity_id": str(r.to_entity_id),
            "relation_type": r.relation_type.value if hasattr(r.relation_type, "value") else r.relation_type,
        }

    def _ser_warning(w: Any) -> dict:
        d: dict[str, Any] = {
            "type": "deprecated_entity",
            "entity_id": str(w.entity_id),
            "message": w.message,
        }
        if w.replacement_entity_id:
            d["replacement_entity_id"] = str(w.replacement_entity_id)
        return d

    return {
        "roots": [_ser_entity(e) for e in bundle.roots],
        "entities": [_ser_entity(e) for e in bundle.entities],
        "contexts": [_ser_context(c) for c in bundle.contexts],
        "relations": [_ser_relation(r) for r in bundle.relations],
        "warnings": [_ser_warning(w) for w in bundle.warnings],
        "ambiguities": bundle.ambiguities,
    }


# ---------------------------------------------------------------------------
# validate_references
# ---------------------------------------------------------------------------


# ---------------------------------------------------------------------------
# get_entity_history
# ---------------------------------------------------------------------------


@mcp.tool(
    description="Retrieve the change history for an entity. Returns revision list in descending order."
)
async def get_entity_history(id: str, limit: int = 20) -> dict:
    entity_id = uuid.UUID(id)

    async with async_session_factory() as session:
        from app.repository.history_repository import HistoryRepository
        hist_repo = HistoryRepository(session)
        items, total = await hist_repo.list_by_entity(entity_id, limit=limit)

    return {
        "entity_id": id,
        "total": total,
        "items": [
            {
                "revision_no": h.revision_no,
                "change_type": h.change_type,
                "changed_fields": h.changed_fields,
                "change_reason": h.change_reason,
                "changed_by": h.changed_by,
                "created_at": h.created_at.isoformat(),
            }
            for h in items
        ],
    }


# ---------------------------------------------------------------------------
# validate_references
# ---------------------------------------------------------------------------


@mcp.tool(
    description=(
        "Validate a list of entity references (UUIDs or aliases). "
        "Returns which references are resolved, ambiguous, or missing."
    )
)
async def validate_references(references: list[str]) -> dict:
    async with async_session_factory() as session:
        result = await ValidateService(session).validate_references(references)

    return {
        "valid": result.valid,
        "resolved": result.resolved,
        "ambiguous": result.ambiguous,
        "missing": result.missing,
    }
