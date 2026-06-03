FROM python:3.12-slim

WORKDIR /app

RUN pip install uv

# Copy source first so the editable install (-e .) can find the `app` package.
# .dockerignore excludes .venv/.env/tests from the build context.
COPY . .
RUN uv pip install --system -e .
RUN chmod +x /app/entrypoint.sh

# Apply DB migrations (alembic upgrade head) on startup, then run the CMD.
ENTRYPOINT ["/app/entrypoint.sh"]
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "2"]
