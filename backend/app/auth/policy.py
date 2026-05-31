from __future__ import annotations

import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.models import ApiKey, UserAccount
from app.exceptions import RegistryError
from app.repository.project_member_repository import ProjectMemberRepository
from app.repository.project_repository import ProjectRepository
from app.repository.user_repository import UserRepository


class AccessPolicy:
    """Centralizes visibility and mutation authorization logic."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._member_repo = ProjectMemberRepository(session)
        self._project_repo = ProjectRepository(session)
        self._user_repo = UserRepository(session)

    async def get_visible_project_ids(
        self,
        user: UserAccount | None,
        api_key: ApiKey | None = None,
    ) -> list[str] | None:
        """Return the project IDs visible to the caller.

        None  → admin (no filter, sees all)
        []    → unauthenticated, legacy key, or user with no memberships
        [ids] → user's active memberships OR single project from api_key
        """
        if api_key is not None:
            if api_key.project_id is not None:
                return [api_key.project_id]
            # project_id=None: check if the issuing user is admin
            if api_key.created_by is not None:
                owner = await self._user_repo.get_by_id(api_key.created_by)
                if owner is not None and owner.role == "admin":
                    return None  # global admin key
            return []  # legacy key — no access

        if user is None:
            return []
        if user.role == "admin":
            return None
        return await self._member_repo.get_project_ids_for_user(user.id)

    async def get_user_project_ids(self, user_id: uuid.UUID) -> list[str]:
        return await self._member_repo.get_project_ids_for_user(user_id)

    def check_can_view_entity(
        self,
        entity_project_id: str | None,
        user: UserAccount | None,
        visible_project_ids: list[str] | None,
    ) -> None:
        """Raise if user cannot view an entity with the given project_id."""
        if entity_project_id is None:
            return
        if visible_project_ids is None:
            return  # admin
        if entity_project_id not in visible_project_ids:
            if user is None:
                raise RegistryError("UNAUTHORIZED", "Authentication required", status_code=401)
            raise RegistryError("FORBIDDEN", "Not a member of this project", status_code=403)

    def check_can_mutate_entity(
        self,
        entity_project_id: str | None,
        user: UserAccount,
        user_project_ids: list[str],
        api_key: ApiKey | None = None,
    ) -> None:
        """Raise if user cannot modify an entity with the given project_id."""
        if api_key is not None:
            if api_key.project_id is not None:
                if entity_project_id != api_key.project_id:
                    raise RegistryError("FORBIDDEN", "API key restricted to a different project", status_code=403)
                return
            # project_id=None on api_key: admin global key passes, legacy key fails
            if user.role == "admin":
                return
            raise RegistryError("FORBIDDEN", "Legacy API key has no write access", status_code=403)

        if user.role == "admin":
            return
        if entity_project_id is None:
            raise RegistryError("FORBIDDEN", "Only admin can modify public entities", status_code=403)
        if entity_project_id not in user_project_ids:
            raise RegistryError("FORBIDDEN", "Not a member of this project", status_code=403)

    async def check_can_assign_project(
        self,
        project_id: str | None,
        user: UserAccount,
    ) -> None:
        """Raise if user cannot create/update an entity with the given project_id.

        - None (public entity): admin only
        - project entity: admin OR project member
        """
        if user.role == "admin":
            if project_id is not None:
                proj = await self._project_repo.get_by_id(project_id)
                if proj is None:
                    raise RegistryError("NOT_FOUND", f"Project '{project_id}' not found", status_code=404)
            return

        if project_id is None:
            raise RegistryError("FORBIDDEN", "Only admin can create public entities", status_code=403)

        proj = await self._project_repo.get_by_id(project_id)
        if proj is None:
            raise RegistryError("NOT_FOUND", f"Project '{project_id}' not found", status_code=404)

        user_project_ids = await self._member_repo.get_project_ids_for_user(user.id)
        if project_id not in user_project_ids:
            raise RegistryError("FORBIDDEN", "Not a member of this project", status_code=403)

    def check_project_manager(
        self,
        project_id: str,
        user: UserAccount,
        user_project_ids: list[str],
        user_project_roles: dict[str, str],
    ) -> None:
        """Raise if user is not an admin or project_admin of the project."""
        if user.role == "admin":
            return
        if project_id not in user_project_ids:
            raise RegistryError("FORBIDDEN", "Not a member of this project", status_code=403)
        if user_project_roles.get(project_id) != "project_admin":
            raise RegistryError("FORBIDDEN", "project_admin role required", status_code=403)
