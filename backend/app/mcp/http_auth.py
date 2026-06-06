"""API key authentication for the mounted MCP streamable-http app.

The MCP app is a sub-ASGI app, so FastAPI ``Depends`` cannot gate it. This pure
ASGI middleware authenticates every HTTP request to ``/mcp`` using the same API
key logic as the REST layer (``AuthService.get_user_by_api_key``), resolves the
caller's project visibility (``AccessPolicy.get_visible_project_ids``), and stows
the result on the ASGI ``scope`` so tools can read it back (see ``scope.py``).
"""
from __future__ import annotations

from starlette.responses import JSONResponse
from starlette.types import ASGIApp, Receive, Scope, Send

from app.auth.policy import AccessPolicy
from app.db.session import async_session_factory
from app.exceptions import RegistryError
from app.mcp.scope import SCOPE_KEY
from app.service.auth_service import AuthService


def _extract_api_key(scope: Scope) -> str | None:
    """Pull the raw API key from Authorization: Bearer or X-API-Key headers."""
    headers = {k.decode("latin-1").lower(): v.decode("latin-1") for k, v in scope.get("headers", [])}
    authorization = headers.get("authorization")
    if authorization and authorization.lower().startswith("bearer "):
        return authorization[7:].strip()
    x_api_key = headers.get("x-api-key")
    if x_api_key:
        return x_api_key.strip()
    return None


async def _send_401(message: str, scope: Scope, receive: Receive, send: Send) -> None:
    response = JSONResponse(
        {"ok": False, "error": {"code": "UNAUTHORIZED", "message": message}},
        status_code=401,
    )
    await response(scope, receive, send)


class McpApiKeyAuthMiddleware:
    """Gate the mounted MCP app behind API key authentication."""

    def __init__(self, app: ASGIApp) -> None:
        self._app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self._app(scope, receive, send)
            return

        raw_key = _extract_api_key(scope)
        if not raw_key:
            await _send_401("API key required", scope, receive, send)
            return

        try:
            async with async_session_factory() as session:
                user, api_key = await AuthService(session).get_user_by_api_key(raw_key)
                visible = await AccessPolicy(session).get_visible_project_ids(user, api_key)
        except RegistryError as exc:
            await _send_401(exc.message, scope, receive, send)
            return

        # Stash the resolved visibility on the scope; the streamable-http transport
        # rebuilds a Request from this same scope, so tools can read it back.
        scope[SCOPE_KEY] = visible
        await self._app(scope, receive, send)
