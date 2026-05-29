from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.models import ProjectMember


class ProjectMemberRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get(self, project_id: str, user_id: uuid.UUID) -> ProjectMember | None:
        result = await self._session.execute(
            select(ProjectMember).where(
                ProjectMember.project_id == project_id,
                ProjectMember.user_id == user_id,
            )
        )
        return result.scalar_one_or_none()

    async def create(
        self,
        *,
        project_id: str,
        user_id: uuid.UUID,
        role: str,
        created_by: uuid.UUID,
    ) -> ProjectMember:
        member = ProjectMember(
            project_id=project_id,
            user_id=user_id,
            role=role,
            created_by=created_by,
        )
        self._session.add(member)
        await self._session.flush()
        return member

    async def update_role(self, member: ProjectMember, role: str) -> ProjectMember:
        member.role = role
        await self._session.flush()
        return member

    async def deactivate(self, member: ProjectMember) -> None:
        member.is_active = False
        await self._session.flush()

    async def list_by_project(self, project_id: str) -> list[ProjectMember]:
        result = await self._session.execute(
            select(ProjectMember).where(
                ProjectMember.project_id == project_id,
                ProjectMember.is_active.is_(True),
            )
        )
        return list(result.scalars())

    async def get_project_ids_for_user(self, user_id: uuid.UUID) -> list[str]:
        result = await self._session.execute(
            select(ProjectMember.project_id).where(
                ProjectMember.user_id == user_id,
                ProjectMember.is_active.is_(True),
            )
        )
        return list(result.scalars())
