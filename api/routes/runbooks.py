"""Runbook listing + detail."""
from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from db.models import Runbook
from db.session import get_db
from rag.retriever import get_runbook_content, retrieve
from schemas import RunbookDetailOut, RunbookOut

router = APIRouter(prefix="/runbooks", tags=["runbooks"])


@router.get("", response_model=list[RunbookOut])
async def list_runbooks(db: AsyncSession = Depends(get_db)) -> list[RunbookOut]:
    result = await db.execute(select(Runbook).order_by(Runbook.slug))
    return [RunbookOut.model_validate(r) for r in result.scalars().all()]


@router.get("/search")
async def search_runbooks(q: str, top_k: int = 5) -> dict:
    if not q.strip():
        raise HTTPException(400, detail="query string 'q' is required")
    if top_k < 1 or top_k > 20:
        raise HTTPException(400, detail="top_k must be between 1 and 20")
    results = await retrieve(q, top_k=top_k)
    return {"query": q, "results": results}


@router.get("/{slug}", response_model=RunbookDetailOut)
async def get_runbook(slug: str, db: AsyncSession = Depends(get_db)) -> RunbookDetailOut:
    result = await db.execute(select(Runbook).where(Runbook.slug == slug))
    rb = result.scalar_one_or_none()
    if rb is None:
        raise HTTPException(404, detail="Runbook not found")
    content = await get_runbook_content(slug)
    return RunbookDetailOut(
        id=rb.id,
        slug=rb.slug,
        title=rb.title,
        risk_level=rb.risk_level,
        indexed_at=rb.indexed_at,
        content=content or "",
    )
