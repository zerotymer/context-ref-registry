from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.models import ApiKey, EntityAuditLog, UserAccount
from app.repository.audit_repository import AuditRepository


def actor_identifier(user: UserAccount | None, api_key: ApiKey | None) -> str:
    if api_key is not None:
        return f"api_key:{api_key.name}"
    if user is not None:
        return user.login_id
    return "system"


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
