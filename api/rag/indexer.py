"""Runbook indexer — reads markdown runbooks, chunks, embeds, stores in Chroma.

Idempotent: re-running updates Chroma and the `runbooks` metadata table.
Invoked from the api Dockerfile CMD at boot (via `python -m rag.indexer`).
"""
from __future__ import annotations

import asyncio
import hashlib
import logging
import re
import uuid
from datetime import datetime, timezone
from pathlib import Path

import chromadb
from chromadb.config import Settings as ChromaSettings
from chromadb.utils.embedding_functions import SentenceTransformerEmbeddingFunction
from sqlalchemy import select

from config import get_settings
from db.models import Runbook
from db.session import session_scope

log = logging.getLogger("ranger.rag.indexer")


FRONTMATTER_RE = re.compile(r"^---\s*\n(?P<fm>.*?)\n---\s*\n(?P<body>.*)$", re.DOTALL)


def _parse_frontmatter(text: str) -> tuple[dict[str, str], str]:
    match = FRONTMATTER_RE.match(text)
    if not match:
        return {}, text
    fm_raw = match.group("fm")
    body = match.group("body")
    fm: dict[str, str] = {}
    for line in fm_raw.splitlines():
        if ":" not in line:
            continue
        k, _, v = line.partition(":")
        fm[k.strip()] = v.strip()
    return fm, body


def _chunk(text: str, target_chars: int = 800, overlap: int = 120) -> list[str]:
    """Split on section headers first, then merge/split to target size."""
    sections = re.split(r"(?=^## )", text, flags=re.MULTILINE)
    sections = [s.strip() for s in sections if s.strip()]

    chunks: list[str] = []
    buffer = ""
    for section in sections:
        if len(buffer) + len(section) + 1 <= target_chars:
            buffer = f"{buffer}\n\n{section}".strip()
        else:
            if buffer:
                chunks.append(buffer)
            if len(section) <= target_chars:
                buffer = section
            else:
                # Long section: sliding window over characters.
                i = 0
                while i < len(section):
                    end = min(i + target_chars, len(section))
                    chunks.append(section[i:end])
                    i = end - overlap if end < len(section) else end
                buffer = ""
    if buffer:
        chunks.append(buffer)
    return chunks


def _collection(chroma_dir: str, collection_name: str, embedding_model: str):
    client = chromadb.PersistentClient(
        path=chroma_dir,
        settings=ChromaSettings(anonymized_telemetry=False),
    )
    embed_fn = SentenceTransformerEmbeddingFunction(model_name=embedding_model)
    return client.get_or_create_collection(
        name=collection_name,
        embedding_function=embed_fn,
        metadata={"hnsw:space": "cosine"},
    )


def _index_sync(
    runbooks_dir: str,
    chroma_dir: str,
    collection_name: str,
    embedding_model: str,
) -> list[dict[str, str]]:
    """Runs inside a threadpool — Chroma + sentence-transformers are sync."""
    col = _collection(chroma_dir, collection_name, embedding_model)
    root = Path(runbooks_dir)
    if not root.exists():
        log.warning("Runbooks dir %s does not exist — nothing to index", runbooks_dir)
        return []

    metadata_rows: list[dict[str, str]] = []
    all_ids: list[str] = []
    all_docs: list[str] = []
    all_metas: list[dict[str, str]] = []

    for md_path in sorted(root.glob("*.md")):
        raw = md_path.read_text(encoding="utf-8")
        fm, body = _parse_frontmatter(raw)
        title = fm.get("title", md_path.stem.replace("-", " ").title())
        risk_level = fm.get("risk_level", "low")
        slug = md_path.stem

        chunks = _chunk(body)
        for i, chunk in enumerate(chunks):
            # Stable ID per (slug, chunk_index, content_hash) so re-index replaces.
            chunk_hash = hashlib.sha1(chunk.encode()).hexdigest()[:10]
            chunk_id = f"{slug}::{i:02d}::{chunk_hash}"
            all_ids.append(chunk_id)
            all_docs.append(chunk)
            all_metas.append(
                {
                    "slug": slug,
                    "title": title,
                    "risk_level": risk_level,
                    "chunk_index": str(i),
                    "source_path": str(md_path),
                }
            )

        metadata_rows.append(
            {
                "slug": slug,
                "title": title,
                "risk_level": risk_level,
                "source_path": str(md_path),
            }
        )

    if not all_ids:
        return metadata_rows

    # Replace-by-id semantics: upsert.
    existing = col.get(ids=all_ids)["ids"]
    if existing:
        col.delete(ids=existing)
    col.add(ids=all_ids, documents=all_docs, metadatas=all_metas)
    log.info("Indexed %d chunks across %d runbooks", len(all_ids), len(metadata_rows))
    return metadata_rows


async def index_runbooks() -> list[dict[str, str]]:
    settings = get_settings()
    rows = await asyncio.to_thread(
        _index_sync,
        settings.runbooks_dir,
        settings.chroma_persist_dir,
        settings.chroma_collection,
        settings.embedding_model,
    )

    # Mirror metadata into Postgres.
    async with session_scope() as session:
        existing = await session.execute(select(Runbook))
        by_slug = {r.slug: r for r in existing.scalars().all()}
        for row in rows:
            rb = by_slug.get(row["slug"])
            if rb:
                rb.title = row["title"]
                rb.risk_level = row["risk_level"]
                rb.source_path = row["source_path"]
                rb.indexed_at = datetime.now(timezone.utc)
            else:
                session.add(
                    Runbook(
                        id=uuid.uuid4(),
                        slug=row["slug"],
                        title=row["title"],
                        risk_level=row["risk_level"],
                        source_path=row["source_path"],
                        indexed_at=datetime.now(timezone.utc),
                    )
                )
    return rows


def main() -> None:
    logging.basicConfig(
        level=get_settings().log_level,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )
    asyncio.run(index_runbooks())


if __name__ == "__main__":
    main()
