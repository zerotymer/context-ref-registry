from __future__ import annotations

from mcp.server.fastmcp import FastMCP

mcp: FastMCP = FastMCP(
    "LLM Reference Registry",
    instructions=(
        "Read-only registry of UI areas, features, and infra units. "
        "Use get_context_bundle as the primary entry point to retrieve rich context. "
        "Never use this server to write or modify data."
    ),
)

# Import tools module to trigger @mcp.tool() registrations
import app.mcp.tools  # noqa: E402, F401

# Mount at /mcp so the streamable-http endpoint is exactly /mcp (the mount adds
# the prefix; without this the endpoint would be /mcp/mcp).
mcp.settings.streamable_http_path = "/"
