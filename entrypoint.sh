#!/bin/sh
set -e

echo "Running database migrations..."
uv run alembic upgrade head

echo "Starting application..."
exec uv run hypercorn src.runtimes.fastapi.main:app --bind [::]

