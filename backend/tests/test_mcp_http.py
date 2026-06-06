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
from app.service.auth_service import AuthService
from app.service.entity_service import EntityService
from app.service.project_service import ProjectService
from app.main import app


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
        yield f"http://127.0.0.1:{port}/mcp"
    finally:
        server.should_exit = True
        await task


async def _make_api_key(*, project_id: str | None, role: str = "admin", suffix: str = "") -> str:
    """Create a user + API key, returning the raw key."""
    async with async_session_factory() as session:
        svc = AuthService(session)
        user = await svc.create_user(
            login_id=f"mcp_http_{role}{suffix}",
            password="pass1234",
            display_name="MCP HTTP",
            role=role,
        )
        _, raw_key = await svc.create_api_key(
            name=f"mcp-http-key{suffix}",
            scopes=["read"],
            project_id=project_id,
            created_by=user.id,
        )
    return raw_key


async def _create_project(project_id: str) -> None:
    async with async_session_factory() as session:
        admin = await AuthService(session).create_user(
            login_id=f"owner_{project_id.lower()}",
            password="pass1234",
            display_name=project_id,
            role="admin",
        )
        await ProjectService(session).create_project(
            id=project_id, alias=project_id, description=None, created_by=admin.id
        )


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


# ---------------------------------------------------------------------------
# Handshake + tool call
# ---------------------------------------------------------------------------


async def test_mcp_handshake_and_list_tools(mcp_url: str):
    key = await _make_api_key(project_id=None, role="admin")
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
    key = await _make_api_key(project_id=None, role="admin")
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
    await _create_project("SCOPEX")
    await _create_project("SCOPEY")

    e_in = await _create_entity(canonical_name="스코프토큰_in", project_id="SCOPEX")
    e_out = await _create_entity(canonical_name="스코프토큰_out", project_id="SCOPEY")
    e_pub = await _create_entity(canonical_name="스코프토큰_pub", project_id=None)

    key = await _make_api_key(project_id="SCOPEX", role="user", suffix="_scoped")
    headers = {"X-API-Key": key}
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
