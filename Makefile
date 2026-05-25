.PHONY: install dev test docker-up docker-down migrate lint

install:
	uv pip install -e ".[dev]"

dev:
	uvicorn app.main:app --reload

test:
	pytest

docker-up:
	docker compose up -d

docker-down:
	docker compose down

migrate:
	alembic upgrade head

lint:
	python -m py_compile app/**/*.py
