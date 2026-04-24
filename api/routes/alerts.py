"""Alert ingestion + listing."""
from __future__ import annotations

import asyncio
import logging
import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from agents.graph import run_triage
from db.models import Alert, AgentRun
from db.session import get_db
from schemas import AlertIn, AlertOut, AlertSubmittedOut

log = logging.getLogger("ranger.routes.alerts")

router = APIRouter(prefix="/alerts", tags=["alerts"])


@router.get("", response_model=list[AlertOut])
async def list_alerts(
    limit: int = 50,
    db: AsyncSession = Depends(get_db),
) -> list[AlertOut]:
    if limit < 1 or limit > 500:
        raise HTTPException(400, detail="limit must be between 1 and 500")
    result = await db.execute(select(Alert).order_by(desc(Alert.created_at)).limit(limit))
    return [AlertOut.model_validate(a) for a in result.scalars().all()]


@router.post("", response_model=AlertSubmittedOut, status_code=202)
async def submit_alert(
    body: AlertIn,
    db: AsyncSession = Depends(get_db),
) -> AlertSubmittedOut:
    alert = Alert(
        device_id=body.device_id,
        alert_type=body.alert_type,
        severity_hint=body.severity_hint,
        payload=body.payload,
    )
    db.add(alert)
    await db.flush()

    run = AgentRun(alert_id=alert.id, status="running")
    db.add(run)
    await db.flush()

    alert_id = alert.id
    run_id = run.id
    await db.commit()

    # Fire-and-forget — the graph writes to DB + WebSocket pubsub itself.
    asyncio.create_task(
        run_triage(
            run_id=run_id,
            alert_id=alert_id,
            device_id=body.device_id,
            alert_type=body.alert_type,
            severity_hint=body.severity_hint,
            payload=body.payload,
        )
    )

    return AlertSubmittedOut(alert_id=alert_id, run_id=run_id)


@router.get("/{alert_id}", response_model=AlertOut)
async def get_alert(alert_id: uuid.UUID, db: AsyncSession = Depends(get_db)) -> AlertOut:
    result = await db.execute(select(Alert).where(Alert.id == alert_id))
    alert = result.scalar_one_or_none()
    if alert is None:
        raise HTTPException(404, detail="Alert not found")
    return AlertOut.model_validate(alert)
