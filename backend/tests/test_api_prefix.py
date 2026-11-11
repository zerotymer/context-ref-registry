"""URL contract: REST/MCP/docs live under /api/v1; only /health stays at root.

A reverse proxy may route `/api/v1/*` straight to the backend (path split) or
everything through the frontend gateway — both rely on this contract.
"""

from httpx import AsyncClient


async def test_rest_served_under_api_prefix(admin_client: AsyncClient):
    assert (await admin_client.get("/api/v1/projects")).status_code == 200


async def test_unprefixed_paths_are_gone(admin_client: AsyncClient):
    # Old root paths would collide with frontend pages (e.g. /entities).
    for path in ("/entities", "/projects", "/auth/me", "/docs", "/openapi.json"):
        assert (await admin_client.get(path)).status_code == 404, path


async def test_docs_and_health_locations(client: AsyncClient):
    assert (await client.get("/api/v1/openapi.json")).status_code == 200
    assert (await client.get("/api/v1/docs")).status_code == 200
    assert (await client.get("/health")).status_code == 200
