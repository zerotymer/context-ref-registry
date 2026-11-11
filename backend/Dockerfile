# syntax=docker/dockerfile:1
#
# Package sources come from the builder's own uv config (index URLs + credentials),
# mounted as a BuildKit secret so it never lands in an image layer:
#   docker build --secret id=uv_config,src=$HOME/.config/uv/uv.toml ./backend

FROM python:3.12-slim AS builder
WORKDIR /app
ENV UV_LINK_MODE=copy UV_COMPILE_BYTECODE=1 PIP_DISABLE_PIP_VERSION_CHECK=1

# Bootstrap uv itself from the default index declared in the same uv config.
RUN --mount=type=secret,id=uv_config,target=/root/.config/uv/uv.toml \
    PIP_INDEX_URL="$(python -c 'import tomllib; idx = tomllib.load(open("/root/.config/uv/uv.toml", "rb"))["index"]; print(next((i for i in idx if i.get("default")), idx[0])["url"])')" \
    pip install --no-cache-dir uv

COPY pyproject.toml uv.lock ./
# Dependencies only — the app source is copied as-is into the runtime image
# (alembic.ini resolves migrations from /app/app/db/migrations).
RUN --mount=type=secret,id=uv_config,target=/root/.config/uv/uv.toml \
    uv sync --frozen --no-dev --no-install-project --no-cache


FROM python:3.12-slim
WORKDIR /app
ENV PATH="/app/.venv/bin:$PATH" PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1

RUN useradd --system --uid 10001 --home-dir /app app \
    && mkdir -p /data && chown app:app /data

COPY --from=builder /app/.venv /app/.venv
COPY alembic.ini entrypoint.sh ./
COPY app ./app
RUN chmod +x /app/entrypoint.sh

USER app
# SQLite DB lives on the mounted volume (registry.db, -wal, -shm).
VOLUME ["/data"]

# Apply DB migrations (alembic upgrade head) on startup, then run the CMD.
ENTRYPOINT ["/app/entrypoint.sh"]
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "2"]
