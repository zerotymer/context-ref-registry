from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.models import EntityAuditLog
from app.repository.audit_repository import AuditRepository

if TYPE_CHECKING:
    from app.auth.dependencies import Actor


def actor_identifier(actor: Actor) -> str:
    return "admin" if actor.is_admin else f"api_key:{actor.api_key.name}"


class AuditService:
    def __init__(self, session: AsyncSession) -> None:
        self._repo = AuditRepository(session)

    async def log(
        self,
        actor: str,
        action: str,
        target_type: str,
        target_id: str,
        before_snapshot: dict | None = None,
        after_snapshot: dict | None = None,
    ) -> EntityAuditLog:
        return await self._repo.create(
            actor=actor,
            action=action,
            target_type=target_type,
            target_id=target_id,
            before_snapshot=before_snapshot,
            after_snapshot=after_snapshot,
        )
