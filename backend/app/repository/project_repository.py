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

    async def list_all(self, *, is_active: bool | None = None, search: str | None = None) -> list[Project]:
        from sqlalchemy import and_

        conditions = []
        if is_active is not None:
            conditions.append(Project.is_active.is_(is_active))
        if search:
            conditions.append(Project.alias.ilike(f"%{search}%") | Project.id.ilike(f"%{search}%"))

        stmt = select(Project)
        if conditions:
            stmt = stmt.where(and_(*conditions))
        stmt = stmt.order_by(Project.id)
        result = await self._session.execute(stmt)
        return list(result.scalars())

    async def update(
        self,
        project: Project,
        *,
        alias: str | None = None,
        description: str | None = None,
        is_active: bool | None = None,
    ) -> Project:
        if alias is not None:
            project.alias = alias
        if description is not None:
            project.description = description
        if is_active is not None:
            project.is_active = is_active
        await self._session.flush()
        await self._session.refresh(project)
        return project
