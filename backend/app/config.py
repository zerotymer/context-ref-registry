import logging
import secrets

from pydantic_settings import BaseSettings

logger = logging.getLogger(__name__)


class Settings(BaseSettings):
    database_url: str = "postgresql+asyncpg://llmref:llmref@localhost:5432/llmref"

    model_config = {"env_file": ".env", "extra": "ignore"}


settings = Settings()

# --- Fixed operational constants (intentionally NOT env-configurable) ---

# JWT signing secret: regenerated on every process start. It is not shared with
# any external service, so a fresh per-process secret is fine — the only effect
# is that existing sessions are invalidated on restart. Logged on startup so
# operators can correlate token validity windows.
JWT_SECRET = secrets.token_hex(32)
JWT_ALGORITHM = "HS256"
JWT_EXPIRE_MINUTES = 60 * 24 * 7  # 7 days

# Initial admin account, created once on startup if no admin exists.
# Fixed to admin/admin by design — rotating it is the operator's responsibility.
BOOTSTRAP_ADMIN_LOGIN_ID = "admin"
BOOTSTRAP_ADMIN_PASSWORD = "admin"
BOOTSTRAP_ADMIN_DISPLAY_NAME = "Admin"

logger.info("JWT secret generated for this process: %s", JWT_SECRET)
