.PHONY: install lock dev test docker-up docker-down migrate lint

install:
	uv pip install -e ".[dev]"

## After changing dependencies: refresh the local uv.lock (gitignored) and the committed
## requirements*.lock (pinned + sha256 hashes, no index URLs) used by the Docker image and CI.
lock:
	uv lock
	uv export --frozen --no-dev --no-emit-project -o requirements.lock
	uv export --frozen --no-dev --extra dev --no-emit-project -o requirements-dev.lock

dev:
	uvicorn app.main:app --reload

test:
	pytest

docker-up:
	docker compose -f ../docker-compose.yml up -d

docker-down:
	docker compose -f ../docker-compose.yml down

migrate:
	alembic upgrade head

lint:
	python -m py_compile app/**/*.py
