"""Access rules.

| caller      | read                              | write                        |
|-------------|-----------------------------------|------------------------------|
| admin       | everything                        | everything                   |
| read key    | own project + public entities     | 403                          |
| write key   | own project + public entities     | own project only (public 403)|
| anonymous   | public entities only              | 401                          |
"""
from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import Actor
from app.exceptions import RegistryError
from app.repository.project_repository import ProjectRepository


def visible_project_ids(actor: Actor | None) -> list[str] | None:
    """None → no filter (admin); [] → public only; [id] → public + that project."""
    if actor is None:
        return []
    if actor.is_admin:
        return None
    return [actor.api_key.project_id]


def check_can_view_entity(entity_project_id: str | None, actor: Actor | None) -> None:
    if entity_project_id is None or (actor is not None and actor.is_admin):
        return
    if actor is None:
        raise RegistryError("UNAUTHORIZED", "Authentication required", status_code=401)
    if entity_project_id != actor.api_key.project_id:
        raise RegistryError("FORBIDDEN", "API key restricted to a different project", status_code=403)


def check_can_mutate_entity(entity_project_id: str | None, actor: Actor) -> None:
    if actor.is_admin:
        return
    if not actor.can_write:
        raise RegistryError("FORBIDDEN", "API key scope 'write' required", status_code=403)
    if entity_project_id is None:
        raise RegistryError("FORBIDDEN", "Only admin can modify public entities", status_code=403)
    if entity_project_id != actor.api_key.project_id:
        raise RegistryError("FORBIDDEN", "API key restricted to a different project", status_code=403)


async def check_can_assign_project(session: AsyncSession, project_id: str | None, actor: Actor) -> None:
    """Raise if the caller cannot create/update an entity under ``project_id``."""
    check_can_mutate_entity(project_id, actor)
    if actor.is_admin and project_id is not None:
        if await ProjectRepository(session).get_by_id(project_id) is None:
            raise RegistryError("NOT_FOUND", f"Project '{project_id}' not found", status_code=404)
