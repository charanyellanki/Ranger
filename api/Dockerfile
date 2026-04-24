FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    HF_HOME=/opt/hf-cache

WORKDIR /app

# System deps for asyncpg / chromadb / sentence-transformers.
RUN apt-get update && apt-get install -y --no-install-recommends \
      build-essential \
      curl \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --upgrade pip && pip install -r requirements.txt

# Pre-download the embedding model so first alert doesn't pay a cold-start tax.
RUN python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')"

COPY . .

EXPOSE 8000

# Entrypoint: wait for DB via healthcheck-gated depends_on, run migrations, seed runbooks, start server.
CMD ["bash", "-c", "alembic upgrade head && python -m rag.indexer && uvicorn main:app --host 0.0.0.0 --port 8000"]
