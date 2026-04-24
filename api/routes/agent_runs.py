"""Agent run + step read endpoints."""
from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from db.models import AgentRun, AgentStep
from db.session import get_db
from schemas import AgentRunOut, AgentStepOut

router = APIRouter(prefix="/runs", tags=["agent_runs"])


@router.get("", response_model=list[AgentRunOut])
async def list_runs(
    alert_id: uuid.UUID | None = None,
    limit: int = 50,
    db: AsyncSession = Depends(get_db),
) -> list[AgentRunOut]:
    if limit < 1 or limit > 500:
        raise HTTPException(400, detail="limit must be between 1 and 500")
    stmt = (
        select(AgentRun)
        .options(selectinload(AgentRun.steps))
        .order_by(desc(AgentRun.started_at))
        .limit(limit)
    )
    if alert_id is not None:
        stmt = stmt.where(AgentRun.alert_id == alert_id)
    result = await db.execute(stmt)
    return [AgentRunOut.model_validate(r) for r in result.scalars().all()]


@router.get("/{run_id}", response_model=AgentRunOut)
async def get_run(run_id: uuid.UUID, db: AsyncSession = Depends(get_db)) -> AgentRunOut:
    stmt = (
        select(AgentRun)
        .options(selectinload(AgentRun.steps))
        .where(AgentRun.id == run_id)
    )
    result = await db.execute(stmt)
    run = result.scalar_one_or_none()
    if run is None:
        raise HTTPException(404, detail="Run not found")
    return AgentRunOut.model_validate(run)


@router.get("/{run_id}/steps", response_model=list[AgentStepOut])
async def get_run_steps(run_id: uuid.UUID, db: AsyncSession = Depends(get_db)) -> list[AgentStepOut]:
    stmt = select(AgentStep).where(AgentStep.run_id == run_id).order_by(AgentStep.step_index)
    result = await db.execute(stmt)
    return [AgentStepOut.model_validate(s) for s in result.scalars().all()]
