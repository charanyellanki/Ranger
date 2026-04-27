#!/usr/bin/env sh
set -e

echo "[entrypoint] applying Alembic migrations"
alembic upgrade head

echo "[entrypoint] indexing runbooks into ChromaDB"
python -m rag.indexer

echo "[entrypoint] starting uvicorn"
# Render (and most PaaS) inject PORT; local docker-compose defaults to 8000.
exec uvicorn main:app --host 0.0.0.0 --port "${PORT:-8000}" --proxy-headers
