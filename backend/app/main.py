import contextlib
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from sqlalchemy import text

from app.api.admin_api_keys import router as admin_api_keys_router
from app.api.admin_projects import router as admin_projects_router
from app.api.admin_users import router as admin_users_router
from app.api.aliases import router as aliases_router
from app.api.auth import router as auth_router
from app.api.bundles import router as bundles_router
from app.api.contexts import router as contexts_router
from app.api.entities import router as entities_router
from app.api.export import router as export_router
from app.api.ingest import router as ingest_router
from app.api.validate import router as validate_router
from app.api.projects import router as projects_router
from app.api.relations import router as relations_router
from app.api.search import router as search_router
from app.api.tags import router as tags_router
from app.db.session import async_session_factory
from app.exceptions import RegistryError
from app.logging_config import configure_logging
from app.middleware import RequestLoggingMiddleware
from app.mcp.http_auth import McpApiKeyAuthMiddleware
from app.mcp.server import mcp
from app.service.auth_service import AuthService

configure_logging()

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    async with contextlib.AsyncExitStack() as stack:
        # Run the MCP streamable-http session manager for the mounted /mcp app.
        await stack.enter_async_context(mcp.session_manager.run())
        # Create the fixed admin/admin account on first startup if no admin exists.
        # Best-effort: never block startup if the DB/schema is not ready yet.
        try:
            async with async_session_factory() as session:
                await AuthService(session).bootstrap_admin()
        except Exception:
            logger.warning("bootstrap_admin skipped (DB not ready?)", exc_info=True)
        yield


app = FastAPI(title="LLM Reference Registry", version="0.1.0", lifespan=lifespan)
app.add_middleware(RequestLoggingMiddleware)

# Read-only MCP server over streamable-http at /mcp, gated by API key auth.
app.mount("/mcp", McpApiKeyAuthMiddleware(mcp.streamable_http_app()))


@app.exception_handler(RegistryError)
async def _registry_error_handler(request: Request, exc: RegistryError) -> JSONResponse:
    error: dict = {"code": exc.code, "message": exc.message}
    if exc.details:
        error["details"] = exc.details
    return JSONResponse(
        status_code=exc.status_code,
        content={"ok": False, "error": error},
    )


app.include_router(auth_router)
app.include_router(admin_users_router)
app.include_router(admin_projects_router)
app.include_router(admin_api_keys_router)
app.include_router(projects_router)
app.include_router(entities_router)
app.include_router(aliases_router)
app.include_router(contexts_router)
app.include_router(relations_router)
app.include_router(ingest_router)
app.include_router(bundles_router)
app.include_router(search_router)
app.include_router(tags_router)
app.include_router(export_router)
app.include_router(validate_router)


@app.get("/health")
async def health() -> JSONResponse:
    db_status = "ok"
    try:
        async with async_session_factory() as session:
            await session.execute(text("SELECT 1"))
    except Exception:
        db_status = "error"

    ok = db_status == "ok"
    return JSONResponse(
        status_code=200 if ok else 503,
        content={
            "ok": ok,
            "data": {
                "status": "healthy" if ok else "degraded",
                "db": db_status,
            },
        },
    )
