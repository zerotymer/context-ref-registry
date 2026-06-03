#!/bin/sh
# Container entrypoint: bring the database schema up to date before the app runs.
#
# `alembic upgrade head` is idempotent — it consults the alembic_version table
# and applies only the revisions that are missing. So an empty database gets the
# full schema created, while an already-current database is a safe no-op with no
# "relation already exists" conflicts. This is why we use migrations here instead
# of metadata.create_all.
#
# The migration runs once, before exec'ing the real command, so even with
# multiple uvicorn workers the schema is established a single time.
set -e

# JWT signing secret must be shared by every uvicorn worker, otherwise a token
# signed by one worker is rejected by another (401) and the frontend loops on
# re-login. We generate it once here and export it so the uvicorn master and all
# forked workers inherit the same value. Operators can pin a stable secret (to
# keep sessions valid across restarts) by setting JWT_SECRET in the environment.
if [ -z "$JWT_SECRET" ]; then
  JWT_SECRET="$(python -c 'import secrets; print(secrets.token_hex(32))')"
  export JWT_SECRET
  echo "[entrypoint] generated ephemeral JWT_SECRET shared across workers (rotates on restart)"
else
  echo "[entrypoint] using JWT_SECRET from environment"
fi

echo "[entrypoint] applying database migrations (alembic upgrade head)..."
alembic upgrade head
echo "[entrypoint] migrations up to date; starting: $*"

exec "$@"
