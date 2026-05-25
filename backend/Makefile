.PHONY: install dev test docker-up docker-down migrate lint

install:
	uv pip install -e ".[dev]"

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
