from __future__ import annotations

import re
import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.models import Project, ProjectMember
from app.exceptions import RegistryError
from app.repository.project_member_repository import ProjectMemberRepository
from app.repository.project_repository import ProjectRepository

_PROJECT_ID_RE = re.compile(r"^[A-Za-z]{3,20}$")

_VALID_ROLES = {"member", "project_admin"}


class ProjectService:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._repo = ProjectRepository(session)
        self._member_repo = ProjectMemberRepository(session)

    async def create_project(
        self,
        *,
        id: str,
        alias: str,
        description: str | None,
        created_by: uuid.UUID,
    ) -> Project:
        if not _PROJECT_ID_RE.match(id):
            raise RegistryError(
                "INVALID_PROJECT_ID",
                "Project ID must be 3-20 alphabetic characters",
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
            id=id, alias=alias, description=description, created_by=created_by
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

    # ------------------------------------------------------------------
    # Membership management
    # ------------------------------------------------------------------

    async def add_member(
        self,
        *,
        project_id: str,
        user_id: uuid.UUID,
        role: str,
        actor_role: str,
        actor_id: uuid.UUID,
    ) -> ProjectMember:
        """Add or re-activate a member.

        actor_role: caller's system role ('admin') or project role ('project_admin', 'member').
        Only admin may assign project_admin role.
        """
        if role not in _VALID_ROLES:
            raise RegistryError("INVALID_ROLE", f"Role must be one of {sorted(_VALID_ROLES)}", status_code=422)

        if role == "project_admin" and actor_role != "admin":
            raise RegistryError(
                "FORBIDDEN", "Only global admin can assign project_admin role", status_code=403
            )

        project = await self.get_project(project_id)
        if not project.is_active:
            raise RegistryError("PROJECT_INACTIVE", f"Project '{project_id}' is inactive", status_code=409)

        existing = await self._member_repo.get(project_id, user_id)
        if existing is not None:
            if existing.is_active:
                raise RegistryError("CONFLICT", "User is already a member", status_code=409)
            existing.is_active = True
            existing.role = role
            await self._session.flush()
            await self._session.commit()
            return existing

        member = await self._member_repo.create(
            project_id=project_id,
            user_id=user_id,
            role=role,
            created_by=actor_id,
        )
        await self._session.commit()
        return member

    async def remove_member(
        self,
        *,
        project_id: str,
        user_id: uuid.UUID,
    ) -> None:
        await self.get_project(project_id)
        member = await self._member_repo.get(project_id, user_id)
        if member is None or not member.is_active:
            raise RegistryError("NOT_FOUND", "Member not found", status_code=404)
        await self._member_repo.deactivate(member)
        await self._session.commit()

    async def update_member_role(
        self,
        *,
        project_id: str,
        user_id: uuid.UUID,
        role: str,
        actor_role: str,
    ) -> ProjectMember:
        if role not in _VALID_ROLES:
            raise RegistryError("INVALID_ROLE", f"Role must be one of {sorted(_VALID_ROLES)}", status_code=422)
        if role == "project_admin" and actor_role != "admin":
            raise RegistryError(
                "FORBIDDEN", "Only global admin can assign project_admin role", status_code=403
            )
        await self.get_project(project_id)
        member = await self._member_repo.get(project_id, user_id)
        if member is None or not member.is_active:
            raise RegistryError("NOT_FOUND", "Member not found", status_code=404)
        await self._member_repo.update_role(member, role)
        await self._session.commit()
        return member

    async def list_members(self, project_id: str) -> list[ProjectMember]:
        await self.get_project(project_id)
        return await self._member_repo.list_by_project(project_id)
