from __future__ import annotations

import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.ref_pattern import RefKind, parse_ref
from app.exceptions import RegistryError
from app.repository.alias_repository import AliasRepository
from app.repository.entity_repository import EntityRepository


class ValidateResult:
    def __init__(self) -> None:
        self.resolved: list[dict] = []
        self.ambiguous: list[dict] = []
        self.missing: list[str] = []

    @property
    def valid(self) -> bool:
        return len(self.ambiguous) == 0 and len(self.missing) == 0


class ValidateService:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._entity_repo = EntityRepository(session)
        self._alias_repo = AliasRepository(session)

    async def validate_references(self, references: list[str]) -> ValidateResult:
        result = ValidateResult()

        for ref in references:
            try:
                parsed = parse_ref(ref)
            except ValueError:
                # Invalid format — treat as alias fallback for backwards compat
                entities = await self._alias_repo.resolve(ref)
                if not entities:
                    result.missing.append(ref)
                elif len(entities) == 1:
                    e = entities[0]
                    result.resolved.append({
                        "input": ref,
                        "status": "resolved",
                        "id": str(e.id),
                        "canonical_name": e.canonical_name,
                        "entity_status": e.status.value if hasattr(e.status, "value") else e.status,
                    })
                else:
                    result.ambiguous.append({
                        "input": ref,
                        "candidates": [str(e.id) for e in entities],
                    })
                continue

            if parsed.kind == RefKind.UUID:
                entity = await self._entity_repo.get_by_id(uuid.UUID(parsed.identifier))
                if entity:
                    result.resolved.append({
                        "input": ref,
                        "status": "resolved",
                        "id": str(entity.id),
                        "canonical_name": entity.canonical_name,
                        "entity_status": entity.status.value if hasattr(entity.status, "value") else entity.status,
                    })
                else:
                    result.missing.append(ref)

            elif parsed.kind == RefKind.SCOPED_UUID:
                entity = await self._entity_repo.get_by_id(uuid.UUID(parsed.identifier))
                if entity is None or entity.project_id != parsed.project_id:
                    result.missing.append(ref)
                else:
                    result.resolved.append({
                        "input": ref,
                        "status": "resolved",
                        "id": str(entity.id),
                        "canonical_name": entity.canonical_name,
                        "entity_status": entity.status.value if hasattr(entity.status, "value") else entity.status,
                    })

            else:  # SCOPED_TAG
                matches = await self._entity_repo.get_by_tag_in_project(parsed.project_id, parsed.identifier)
                if not matches:
                    result.missing.append(ref)
                elif len(matches) == 1:
                    e = matches[0]
                    result.resolved.append({
                        "input": ref,
                        "status": "resolved",
                        "id": str(e.id),
                        "canonical_name": e.canonical_name,
                        "entity_status": e.status.value if hasattr(e.status, "value") else e.status,
                    })
                else:
                    result.ambiguous.append({
                        "input": ref,
                        "candidates": [str(e.id) for e in matches],
                    })

        return result
