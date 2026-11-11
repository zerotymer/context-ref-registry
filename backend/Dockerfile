# syntax=docker/dockerfile:1
#
# Dependencies are installed from requirements.lock (pinned versions + sha256 hashes,
# no index URLs). The package index comes from the builder's own uv config, mounted
# as a BuildKit secret so it never lands in an image layer:
#   docker build --secret id=uv_config,src=$HOME/.config/uv/uv.toml ./backend

FROM python:3.12-slim AS builder
WORKDIR /app
ENV PIP_DISABLE_PIP_VERSION_CHECK=1

COPY requirements.lock ./
# Use the default index declared in the builder's uv config; --require-hashes rejects
# any artifact whose hash is not in requirements.lock.
RUN --mount=type=secret,id=uv_config,target=/run/secrets/uv.toml \
    python -m venv /app/.venv \
    && PIP_INDEX_URL="$(python -c 'import tomllib; idx = tomllib.load(open("/run/secrets/uv.toml", "rb"))["index"]; print(next((i for i in idx if i.get("default")), idx[0])["url"])')" \
       /app/.venv/bin/pip install --no-cache-dir --require-hashes -r requirements.lock


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
