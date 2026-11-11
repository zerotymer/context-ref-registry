from __future__ import annotations

import re
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.models import Project
from app.exceptions import RegistryError
from app.repository.project_repository import ProjectRepository

_PROJECT_ID_RE = re.compile(r"^[A-Za-z0-9_]{3,50}$")


class ProjectService:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._repo = ProjectRepository(session)

    async def create_project(
        self,
        *,
        id: str,
        alias: str,
        description: str | None,
    ) -> Project:
        if not _PROJECT_ID_RE.match(id):
            raise RegistryError(
                "INVALID_PROJECT_ID",
                "Project ID must be 3-50 characters: letters, digits, underscore (_)",
                status_code=422,
            )
        alias = alias.strip()
        if not alias or len(alias) > 50:
            raise RegistryError(
                "INVALID_ALIAS",
                "Project alias must be 1-50 characters after trimming",
                status_code=422,
            )
        if await self._repo.get_by_id(id) is not None:
            raise RegistryError("CONFLICT", f"Project '{id}' already exists", status_code=409)

        project = await self._repo.create(
            id=id, alias=alias, description=description
        )
        await self._session.commit()
        return project

    async def get_project(self, project_id: str) -> Project:
        project = await self._repo.get_by_id(project_id)
        if project is None:
            raise RegistryError("NOT_FOUND", f"Project '{project_id}' not found", status_code=404)
        return project

    async def list_projects(self) -> list[Project]:
        return await self._repo.list_active()

    async def list_all_projects(
        self,
        *,
        is_active: bool | None = None,
        search: str | None = None,
    ) -> list[Project]:
        return await self._repo.list_all(is_active=is_active, search=search)

    async def update_project(
        self,
        project_id: str,
        *,
        alias: str | None = None,
        description: str | None = None,
        is_active: bool | None = None,
    ) -> Project:
        project = await self.get_project(project_id)
        if alias is not None:
            alias = alias.strip()
            if not alias or len(alias) > 50:
                raise RegistryError(
                    "INVALID_ALIAS",
                    "Project alias must be 1-50 characters after trimming",
                    status_code=422,
                )
        updated = await self._repo.update(project, alias=alias, description=description, is_active=is_active)
        await self._session.commit()
        return updated
