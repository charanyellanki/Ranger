"""Chroma retriever. Async-safe via to_thread.

Caches the collection handle at module scope to avoid re-opening the client
on every query.
"""
from __future__ import annotations

import asyncio
import logging
from pathlib import Path
from typing import Any

import chromadb
from chromadb.config import Settings as ChromaSettings
from chromadb.utils.embedding_functions import SentenceTransformerEmbeddingFunction

from config import get_settings

log = logging.getLogger("ranger.rag.retriever")

_collection: Any = None


def _get_collection():
    global _collection
    if _collection is not None:
        return _collection
    s = get_settings()
    client = chromadb.PersistentClient(
        path=s.chroma_persist_dir,
        settings=ChromaSettings(anonymized_telemetry=False),
    )
    embed_fn = SentenceTransformerEmbeddingFunction(model_name=s.embedding_model)
    _collection = client.get_or_create_collection(
        name=s.chroma_collection,
        embedding_function=embed_fn,
        metadata={"hnsw:space": "cosine"},
    )
    return _collection


def _query_sync(query_text: str, top_k: int) -> list[dict[str, Any]]:
    col = _get_collection()
    result = col.query(query_texts=[query_text], n_results=top_k)
    ids = result.get("ids", [[]])[0]
    docs = result.get("documents", [[]])[0]
    metas = result.get("metadatas", [[]])[0]
    distances = result.get("distances", [[]])[0] or [None] * len(ids)

    # Dedupe by runbook slug — keep the best-scoring chunk per runbook.
    by_slug: dict[str, dict[str, Any]] = {}
    for cid, doc, meta, dist in zip(ids, docs, metas, distances):
        slug = meta.get("slug", cid)
        score = 1.0 - dist if dist is not None else 0.0
        if slug not in by_slug or score > by_slug[slug]["score"]:
            by_slug[slug] = {
                "chunk_id": cid,
                "slug": slug,
                "title": meta.get("title", slug),
                "risk_level": meta.get("risk_level", "low"),
                "score": round(score, 4),
                "excerpt": doc[:600],
            }
    return sorted(by_slug.values(), key=lambda r: r["score"], reverse=True)


async def retrieve(query_text: str, top_k: int = 3) -> list[dict[str, Any]]:
    return await asyncio.to_thread(_query_sync, query_text, top_k)


async def get_runbook_content(slug: str) -> str | None:
    """Read the original markdown for a runbook (for the detail view)."""
    s = get_settings()
    path = Path(s.runbooks_dir) / f"{slug}.md"
    if not path.exists():
        return None
    return await asyncio.to_thread(path.read_text, "utf-8")
