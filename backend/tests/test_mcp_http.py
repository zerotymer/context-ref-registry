"""End-to-end tests for the MCP streamable-http transport.

Unlike test_mcp_tools.py (which calls tool functions directly), these boot the
FastAPI app under a real uvicorn server and drive it with an MCP client over
HTTP — exercising the mount, the API-key auth middleware, the session manager
handshake, and per-request project scoping.
"""
from __future__ import annotations

import asyncio
import json
import socket

import httpx
import pytest
import uvicorn
from mcp import ClientSession
from mcp.client.streamable_http import streamablehttp_client

from app.db.session import async_session_factory
from app.domain.schemas import EntityCreate
from app.service.entity_service import EntityService
from app.main import app
from app.mcp.server import build_transport_security, mcp
from tests.conftest import create_key, create_project


def _free_port() -> int:
    sock = socket.socket()
    sock.bind(("127.0.0.1", 0))
    port = sock.getsockname()[1]
    sock.close()
    return port


@pytest.fixture(scope="module")
async def mcp_url():
    """Boot the app under uvicorn (lifespan on) and yield the /mcp URL.

    Module-scoped: the MCP streamable-http session manager can only be started
    once per process, so the server is shared across the module's tests.
    """
    port = _free_port()
    config = uvicorn.Config(app, host="127.0.0.1", port=port, log_level="warning", lifespan="on")
    server = uvicorn.Server(config)
    # Don't hijack pytest's signal handlers from the main thread.
    server.install_signal_handlers = lambda: None  # type: ignore[method-assign]
    task = asyncio.create_task(server.serve())
    try:
        for _ in range(100):
            if server.started:
                break
            await asyncio.sleep(0.05)
        else:  # pragma: no cover
            raise RuntimeError("uvicorn server did not start")
        yield f"http://127.0.0.1:{port}/api/v1/mcp"
    finally:
        server.should_exit = True
        await task


async def _make_api_key(*, project_id: str = "MCPHTTP", scope: str = "read") -> str:
    return await create_key(project_id, scope)


async def _create_entity(*, canonical_name: str, project_id: str | None) -> str:
    async with async_session_factory() as session:
        entity = await EntityService(session).create(
            EntityCreate(type="FEATURE", canonical_name=canonical_name, project_id=project_id)
        )
        await session.commit()
        return str(entity.id)


def _tool_payload(result) -> dict:
    """Parse the JSON dict a tool returned from its first text content block."""
    return json.loads(result.content[0].text)


# ---------------------------------------------------------------------------
# Auth middleware
# ---------------------------------------------------------------------------


async def test_mcp_requires_api_key(mcp_url: str):
    """A request with no API key is rejected with 401 before any MCP handling."""
    async with httpx.AsyncClient(follow_redirects=True) as client:
        resp = await client.post(
            mcp_url,
            headers={"Accept": "application/json, text/event-stream", "Content-Type": "application/json"},
            json={"jsonrpc": "2.0", "id": 1, "method": "ping"},
        )
    assert resp.status_code == 401
    assert resp.json()["error"]["code"] == "UNAUTHORIZED"


async def test_mcp_invalid_api_key(mcp_url: str):
    async with httpx.AsyncClient(follow_redirects=True) as client:
        resp = await client.post(
            mcp_url,
            headers={
                "Accept": "application/json, text/event-stream",
                "Content-Type": "application/json",
                "Authorization": "Bearer not-a-real-key",
            },
            json={"jsonrpc": "2.0", "id": 1, "method": "ping"},
        )
    assert resp.status_code == 401


async def test_mcp_rejects_x_api_key_header(mcp_url: str):
    """X-API-Key is no longer accepted — only Authorization: Bearer."""
    key = await _make_api_key()
    async with httpx.AsyncClient(follow_redirects=True) as client:
        resp = await client.post(
            mcp_url,
            headers={
                "Accept": "application/json, text/event-stream",
                "Content-Type": "application/json",
                "X-API-Key": key,
            },
            json={"jsonrpc": "2.0", "id": 1, "method": "ping"},
        )
    assert resp.status_code == 401


# ---------------------------------------------------------------------------
# Handshake + tool call
# ---------------------------------------------------------------------------


async def test_mcp_handshake_and_list_tools(mcp_url: str):
    key = await _make_api_key()
    headers = {"Authorization": f"Bearer {key}"}
    async with streamablehttp_client(mcp_url, headers=headers) as (read, write, _):
        async with ClientSession(read, write) as session:
            await session.initialize()
            tools = await session.list_tools()

    names = {t.name for t in tools.tools}
    assert {
        "resolve_alias",
        "get_entity",
        "search_entities",
        "get_related_entities",
        "get_context_bundle",
        "get_entity_history",
        "validate_references",
    } <= names


async def test_mcp_tool_call_end_to_end(mcp_url: str):
    key = await _make_api_key()
    entity_id = await _create_entity(canonical_name="검색가능한공개기능", project_id=None)

    headers = {"Authorization": f"Bearer {key}"}
    async with streamablehttp_client(mcp_url, headers=headers) as (read, write, _):
        async with ClientSession(read, write) as session:
            await session.initialize()
            result = await session.call_tool("search_entities", {"query": "검색가능한공개기능"})

    payload = _tool_payload(result)
    ids = [r["id"] for r in payload["results"]]
    assert entity_id in ids


# ---------------------------------------------------------------------------
# Project scoping
# ---------------------------------------------------------------------------


async def test_mcp_project_scope_filters_tools(mcp_url: str):
    """A project-scoped API key sees public + in-scope entities, never out-of-scope ones."""
    await create_project("SCOPEX")
    await create_project("SCOPEY")

    e_in = await _create_entity(canonical_name="스코프토큰_in", project_id="SCOPEX")
    e_out = await _create_entity(canonical_name="스코프토큰_out", project_id="SCOPEY")
    e_pub = await _create_entity(canonical_name="스코프토큰_pub", project_id=None)

    key = await _make_api_key(project_id="SCOPEX")
    headers = {"Authorization": f"Bearer {key}"}
    async with streamablehttp_client(mcp_url, headers=headers) as (read, write, _):
        async with ClientSession(read, write) as session:
            await session.initialize()

            search = _tool_payload(await session.call_tool("search_entities", {"query": "스코프토큰"}))
            seen = {r["id"] for r in search["results"]}
            assert e_in in seen
            assert e_pub in seen
            assert e_out not in seen

            # In-scope entity is retrievable.
            got_in = _tool_payload(await session.call_tool("get_entity", {"id": e_in}))
            assert got_in["entity"]["id"] == e_in

            # Out-of-scope entity is hidden as not-found.
            got_out = _tool_payload(await session.call_tool("get_entity", {"id": e_out}))
            assert got_out.get("error") == "ENTITY_NOT_FOUND"

            # validate_references re-classifies the out-of-scope id as missing.
            validated = _tool_payload(
                await session.call_tool("validate_references", {"references": [e_in, e_out]})
            )
            resolved_ids = [r["id"] for r in validated["resolved"]]
            assert e_in in resolved_ids
            assert e_out in validated["missing"]
            assert validated["valid"] is False


# ---------------------------------------------------------------------------
# Host header allowlist (DNS rebinding protection)
# ---------------------------------------------------------------------------


def test_transport_security_defaults_to_localhost_and_accepts_extras():
    default = build_transport_security("")
    assert default.allowed_hosts == ["127.0.0.1:*", "localhost:*", "[::1]:*"]

    extra = build_transport_security(" api:* , mcp.example.com ,")
    assert extra.allowed_hosts[-2:] == ["api:*", "mcp.example.com"]
    assert "https://mcp.example.com" in extra.allowed_origins


async def _initialize_status(mcp_url: str, host: str) -> int:
    key = await _make_api_key()
    async with httpx.AsyncClient() as client:
        resp = await client.post(
            mcp_url + "/",
            headers={
                "Host": host,
                "Authorization": f"Bearer {key}",
                "Accept": "application/json, text/event-stream",
                "Content-Type": "application/json",
            },
            json={
                "jsonrpc": "2.0", "id": 1, "method": "initialize",
                "params": {"protocolVersion": "2025-03-26", "capabilities": {},
                           "clientInfo": {"name": "t", "version": "0"}},
            },
        )
    return resp.status_code


async def test_mcp_rejects_unlisted_host(mcp_url: str):
    assert await _initialize_status(mcp_url, "api:8000") == 421


async def test_mcp_accepts_configured_host(mcp_url: str, monkeypatch: pytest.MonkeyPatch):
    # The transport holds this settings object by reference, so patching it applies live.
    security = mcp.settings.transport_security
    monkeypatch.setattr(security, "allowed_hosts", [*security.allowed_hosts, "api:*"])
    assert await _initialize_status(mcp_url, "api:8000") == 200
