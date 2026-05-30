from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.enums import EntityType, Locale
from app.domain.schemas import (
    BundleContextRead,
    BundleEntityRead,
    BundleRelationRead,
    ContextBundleRequest,
    ContextBundleResponse,
    DeprecatedWarning,
)
from app.service.bundle_service import BundleService

_TYPE_ORDER = [
    EntityType.UI_AREA,
    EntityType.FEATURE,
    EntityType.INFRA_UNIT,
    EntityType.API,
    EntityType.CODE_SYMBOL,
]


class ExportService:
    def __init__(self, session: AsyncSession) -> None:
        self._bundle_service = BundleService(session)

    async def generate_agents_md(
        self,
        root_ids: list[uuid.UUID],
        max_depth: int,
        token_budget: int,
        language: Locale,
    ) -> str:
        req = ContextBundleRequest(
            root_ids=root_ids,
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
