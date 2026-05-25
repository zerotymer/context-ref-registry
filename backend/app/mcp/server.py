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


if __name__ == "__main__":
    # Read-only registry server over stdio. MCP clients spawn this process.
    mcp.run()
