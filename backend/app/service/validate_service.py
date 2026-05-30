from __future__ import annotations

import uuid

from sqlalchemy.ext.asyncio import AsyncSession

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
            # Try as UUID first
            try:
                uid = uuid.UUID(ref)
                entity = await self._entity_repo.get_by_id(uid)
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
                continue
            except ValueError:
                pass

            # Try as alias
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

        return result
