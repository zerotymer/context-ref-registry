from __future__ import annotations

import re
import uuid
from datetime import datetime, timezone

from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.enums import ContextType, EntityStatus, EntityType, Locale
from app.domain.models import Entity, EntityContext, EntityMetadata
from app.domain.schemas import (
    BundleContextRead,
    BundleEntityRead,
    BundleRelationRead,
    ContextBundleRequest,
    ContextBundleResponse,
    DeprecatedWarning,
)
from app.repository.context_repository import ContextRepository
from app.repository.entity_repository import EntityRepository
from app.service.bundle_service import BundleService

_TYPE_ORDER = [
    EntityType.UI_AREA,
    EntityType.FEATURE,
    EntityType.INFRA_UNIT,
    EntityType.API,
    EntityType.CODE_SYMBOL,
]

_HTTP_METHODS = {"GET", "POST", "PUT", "PATCH", "DELETE", "HEAD", "OPTIONS"}
_METHOD_RE = re.compile(r"^(GET|POST|PUT|PATCH|DELETE|HEAD|OPTIONS)\s+(/\S*)", re.IGNORECASE)

_DESCRIPTION_CONTEXT_TYPES = [
    ContextType.DETAILS,
    ContextType.IMPLEMENTATION_HINT,
    ContextType.BUSINESS_RULE,
    ContextType.VALIDATION_RULE,
    ContextType.SECURITY_NOTE,
    ContextType.INFRA_NOTE,
    ContextType.EXCEPTION_CASE,
    ContextType.COMPATIBILITY_NOTE,
]


class ExportService:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._bundle_service = BundleService(session)

    async def generate_openapi(
        self,
        include_deprecated: bool = False,
        title: str = "Context Registry — API Entities",
        version: str = "generated",
    ) -> dict:
        entity_repo = EntityRepository(self._session)
        context_repo = ContextRepository(self._session)

        all_entities, _ = await entity_repo.list(
            types=[EntityType.API],
            limit=1000,
            offset=0,
        )

        paths: dict[str, dict] = {}

        for entity in all_entities:
            if entity.status == EntityStatus.DEPRECATED.value and not include_deprecated:
                continue

            contexts = await context_repo.list_by_entity(entity.id)
            method, path = _extract_method_and_path(entity, contexts)

            operation = _build_operation(entity, contexts)

            paths.setdefault(path, {})[method] = operation

        return {
            "openapi": "3.1.0",
            "info": {
                "title": title,
                "version": version,
                "description": f"Auto-generated from Context Ref Registry on {datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')}",
            },
            "paths": paths,
        }

    async def generate_agents_md(
        self,
        root_ids: list[uuid.UUID],
        max_depth: int,
        token_budget: int,
        language: Locale,
    ) -> str:
        req = ContextBundleRequest(
            root_ids=[str(rid) for rid in root_ids],
            max_depth=max_depth,
            token_budget=token_budget,
            language=language,
        )
        bundle = await self._bundle_service.get_context_bundle(req)
        return _render_agents_md(bundle)


def _render_agents_md(bundle: ContextBundleResponse) -> str:
    lines: list[str] = []

    lines.append("# Context Registry")
    lines.append("")
    now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    lines.append(f"> Generated: {now}")
    lines.append("")

    if bundle.warnings:
        lines.append("## ⚠️ Deprecated Entities")
        lines.append("")
        for w in bundle.warnings:
            line = f"- `{w.entity_id}` — deprecated"
            if w.replacement_entity_id:
                line += f", replaced by `{w.replacement_entity_id}`"
            lines.append(line)
        lines.append("")
        lines.append("---")
        lines.append("")

    all_entities: list[BundleEntityRead] = bundle.roots + bundle.entities

    context_map: dict[uuid.UUID, list[BundleContextRead]] = {}
    for ctx in bundle.contexts:
        context_map.setdefault(ctx.entity_id, []).append(ctx)

    entities_by_type: dict[EntityType, list[BundleEntityRead]] = {}
    for entity in all_entities:
        entities_by_type.setdefault(entity.type, []).append(entity)

    for etype in _TYPE_ORDER:
        group = entities_by_type.get(etype)
        if not group:
            continue

        lines.append(f"## {etype.value}")
        lines.append("")

        for entity in group:
            lines.append(f"### {entity.canonical_name}")
            lines.append("")
            lines.append(f"- **ID**: `{entity.id}`")
            lines.append(f"- **Status**: {entity.status.value}")
            lines.append("")

            ctxs = context_map.get(entity.id, [])
            for ctx in ctxs:
                lines.append(f"#### {ctx.context_type.value}")
                lines.append("")
                lines.append(ctx.body)
                lines.append("")

        lines.append("---")
        lines.append("")

    if bundle.relations:
        lines.append("## Relations")
        lines.append("")
        lines.append("| From | Type | To |")
        lines.append("|------|------|----|")
        for rel in bundle.relations:
            lines.append(f"| `{rel.from_entity_id}` | {rel.relation_type.value} | `{rel.to_entity_id}` |")
        lines.append("")

    return "\n".join(lines)


def _extract_method_and_path(entity: Entity, contexts: list[EntityContext]) -> tuple[str, str]:
    # 1. Check entity_metadata for explicit api meta
    for meta in entity.metadata_entries:
        if meta.meta_type == "api" and isinstance(meta.data, dict):
            method = str(meta.data.get("method", "")).upper()
            path = meta.data.get("path", "")
            if method in _HTTP_METHODS and path:
                return method.lower(), path

    # 2. Parse canonical_name as "METHOD /path"
    m = _METHOD_RE.match(entity.canonical_name.strip())
    if m:
        return m.group(1).lower(), m.group(2)

    # 3. Fallback: use slugified canonical_name as GET path
    slug = re.sub(r"[^\w\-]", "-", entity.canonical_name.strip().lower())
    slug = re.sub(r"-+", "-", slug).strip("-")
    return "get", f"/{slug}"


def _build_operation(entity: Entity, contexts: list[EntityContext]) -> dict:
    summary: str | None = None
    description_parts: list[str] = []

    if entity.description:
        description_parts.append(entity.description)

    for ctx in contexts:
        if ctx.context_type == ContextType.SUMMARY.value and summary is None:
            summary = ctx.body
        elif ctx.context_type in {ct.value for ct in _DESCRIPTION_CONTEXT_TYPES}:
            description_parts.append(f"**{ctx.context_type}**\n\n{ctx.body}")

    operation: dict = {
        "operationId": str(entity.id),
        "tags": [t.tag for t in entity.tags],
    }

    if summary is not None:
        operation["summary"] = summary
    else:
        operation["summary"] = entity.canonical_name

    if description_parts:
        operation["description"] = "\n\n---\n\n".join(description_parts)

    if entity.status == EntityStatus.DEPRECATED.value:
        operation["deprecated"] = True

    # Check metadata for parameters/request_body/responses
    for meta in entity.metadata_entries:
        if meta.meta_type == "api" and isinstance(meta.data, dict):
            if "parameters" in meta.data:
                operation["parameters"] = meta.data["parameters"]
            if "request_body" in meta.data:
                operation["requestBody"] = meta.data["request_body"]
            if "responses" in meta.data:
                operation["responses"] = meta.data["responses"]
            break

    if "responses" not in operation:
        operation["responses"] = {"200": {"description": "Success"}}

    return operation
