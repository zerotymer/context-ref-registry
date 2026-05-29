from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.models import Project


class ProjectRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(
        self,
        *,
        id: str,
        alias: str,
        description: str | None,
        created_by: uuid.UUID,
    ) -> Project:
        project = Project(id=id, alias=alias, description=description, created_by=created_by)
        self._session.add(project)
        await self._session.flush()
        await self._session.refresh(project)
        return project

    async def get_by_id(self, project_id: str) -> Project | None:
        result = await self._session.execute(
            select(Project).where(Project.id == project_id)
        )
        return result.scalar_one_or_none()

    async def list_active(self) -> list[Project]:
        result = await self._session.execute(
            select(Project).where(Project.is_active.is_(True)).order_by(Project.id)
        )
        return list(result.scalars())
