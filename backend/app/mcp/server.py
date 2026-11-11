from __future__ import annotations

from mcp.server.fastmcp import FastMCP
from mcp.server.transport_security import TransportSecuritySettings

from app.config import settings

_LOCAL_HOSTS = ["127.0.0.1:*", "localhost:*", "[::1]:*"]


def build_transport_security(extra_hosts: str = "") -> TransportSecuritySettings:
    """DNS rebinding protection: localhost always, plus comma-separated extra hosts.

    Host patterns: exact ("mcp.example.com") or any port ("api:*").
    """
    hosts = _LOCAL_HOSTS + [h.strip() for h in extra_hosts.split(",") if h.strip()]
    return TransportSecuritySettings(
        enable_dns_rebinding_protection=True,
        allowed_hosts=hosts,
        allowed_origins=[f"{scheme}://{h}" for h in hosts for scheme in ("http", "https")],
    )


mcp: FastMCP = FastMCP(
    name="LLM Reference Registry",
    instructions=(
        "Read-only registry of UI areas, features, and infra units. "
        "Use get_context_bundle as the primary entry point to retrieve rich context. "
        "Never use this server to write or modify data."
    ),
    transport_security=build_transport_security(settings.mcp_allowed_hosts),
)

# Import tools module to trigger @mcp.tool() registrations
import app.mcp.tools  # noqa: E402, F401

# Mount at /mcp so the streamable-http endpoint is exactly /mcp (the mount adds
# the prefix; without this the endpoint would be /mcp/mcp).
mcp.settings.streamable_http_path = "/"
