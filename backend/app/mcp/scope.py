"""Per-request project visibility scope for MCP tools.

The HTTP auth middleware (`http_auth.py`) authenticates the API key and stashes
the caller's visible project IDs onto the ASGI ``scope`` under ``SCOPE_KEY``.
The streamable-http transport builds a Starlette ``Request`` from that same scope
and threads it into the MCP request context, so tools can read the scope back via
``mcp.get_context().request_context.request``.

Scope semantics mirror ``AccessPolicy.get_visible_project_ids`` / the repository
``_apply_visibility`` helper:

    None   → no scoping (admin / direct in-process call): everything is visible.
    []     → public entities only (``project_id IS NULL``).
    [ids]  → public entities plus the listed projects.
"""
from __future__ import annotations

from app.mcp.server import mcp

# ASGI scope key carrying the authenticated caller's visible project IDs.
SCOPE_KEY = "mcp_visible_project_ids"


def current_visible_project_ids() -> list[str] | None:
    """Return the visible project IDs for the active MCP request.

    Returns ``None`` when there is no request context (e.g. tools invoked
    directly via ``mcp.call_tool`` in tests), which means "no scoping".
    """
    ctx = mcp.get_context()
    try:
        request = ctx.request_context.request
    except ValueError:
        return None
    if request is None:
        return None
    return request.scope.get(SCOPE_KEY)


def is_visible(entity_project_id: str | None, visible_project_ids: list[str] | None) -> bool:
    """Whether an entity with the given project_id is visible to the caller."""
    if visible_project_ids is None:
        return True  # admin / no scoping
    if entity_project_id is None:
        return True  # public entity
    return entity_project_id in visible_project_ids
