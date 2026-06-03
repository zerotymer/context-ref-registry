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

echo "[entrypoint] applying database migrations (alembic upgrade head)..."
alembic upgrade head
echo "[entrypoint] migrations up to date; starting: $*"

exec "$@"
