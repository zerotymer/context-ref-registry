import logging
import os
import secrets

from pydantic_settings import BaseSettings

logger = logging.getLogger(__name__)


class Settings(BaseSettings):
    database_url: str = "postgresql+asyncpg://llmref:llmref@localhost:5432/llmref"

    model_config = {"env_file": ".env", "extra": "ignore"}


settings = Settings()

# --- Fixed operational constants (intentionally NOT env-configurable) ---

# JWT signing secret. MUST be identical across every worker process, otherwise a
# token signed by one worker is rejected by another (round-robin) with a 401,
# which drives the frontend into an infinite re-login loop. Because uvicorn
# --workers spawns independent processes, we cannot rely on a per-process random
# value here. The secret is sourced from the JWT_SECRET environment variable,
# which entrypoint.sh generates once and exports so all workers inherit the same
# value (rotating on container restart). The per-process fallback below only
# applies to single-process local runs that set no env var.
JWT_SECRET = os.environ.get("JWT_SECRET") or secrets.token_hex(32)
JWT_ALGORITHM = "HS256"
JWT_EXPIRE_MINUTES = 60 * 24 * 7  # 7 days

# Initial admin account, created once on startup if no admin exists.
# Fixed to admin/admin by design — rotating it is the operator's responsibility.
BOOTSTRAP_ADMIN_LOGIN_ID = "admin"
BOOTSTRAP_ADMIN_PASSWORD = "admin"
BOOTSTRAP_ADMIN_DISPLAY_NAME = "Admin"

# Do not log the secret itself; only whether it came from the environment.
logger.info(
    "JWT secret loaded (source=%s)",
    "env" if os.environ.get("JWT_SECRET") else "per-process-fallback",
)
