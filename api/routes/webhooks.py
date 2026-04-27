"""Inbound webhooks from external systems (e.g. SignalGuard)."""
from __future__ import annotations

import asyncio
import logging
from datetime import datetime
from typing import Any

from fastapi import APIRouter, Header, HTTPException, Depends
from pydantic import BaseModel, ConfigDict
from sqlalchemy.ext.asyncio import AsyncSession

from agents.graph import run_triage
from config import get_settings
from db.models import AgentRun, Alert
from db.session import get_db
from schemas import AlertSubmittedOut

log = logging.getLogger("ranger.routes.webhooks")

router = APIRouter(prefix="/webhooks", tags=["webhooks"])


class SignalGuardAnomaly(BaseModel):
    """Mirrors SignalGuard's AnomalyRecord — only the fields Ranger needs."""

    model_config = ConfigDict(extra="ignore")

    id: int
    device_id: str
    customer_id: str | None = None
    customer_name: str | None = None
    site_id: str | None = None
    site_name: str | None = None
    gateway_id: str | None = None
    building: str | None = None
    unit_id: str | None = None
    timestamp: datetime
    anomaly_type: str
    detected_by_model: str
    severity: str
    raw_payload: dict[str, Any] = {}
    reason: str | None = None
    status: str = "dispatched"
    assignee: str | None = None
    action_note: str | None = None


def _map_severity(sg_severity: str) -> str | None:
    """SignalGuard uses low/medium/high; Ranger adds critical."""
    if sg_severity in ("low", "medium", "high", "critical"):
        return sg_severity
    return None


@router.post("/signalguard", response_model=AlertSubmittedOut, status_code=202)
async def receive_signalguard_dispatch(
    body: SignalGuardAnomaly,
    db: AsyncSession = Depends(get_db),
    x_webhook_secret: str = Header(""),
) -> AlertSubmittedOut:
    """Receive a dispatched anomaly from SignalGuard and start agentic triage."""
    settings = get_settings()

    expected = settings.signalguard_webhook_secret
    if expected and x_webhook_secret != expected:
        raise HTTPException(status_code=401, detail="invalid webhook secret")

    payload: dict[str, Any] = {
        **body.raw_payload,
        "customer_id": body.customer_id,
        "customer_name": body.customer_name,
        "site_id": body.site_id,
        "site_name": body.site_name,
        "gateway_id": body.gateway_id,
        "building": body.building,
        "unit_id": body.unit_id,
        "detected_by_model": body.detected_by_model,
        "reason": body.reason,
        "signalguard_assignee": body.assignee,
        "signalguard_note": body.action_note,
        "signalguard_timestamp": body.timestamp.isoformat(),
    }

    alert = Alert(
        device_id=body.device_id,
        alert_type=body.anomaly_type,
        severity_hint=_map_severity(body.severity),
        payload=payload,
        source="signalguard",
        source_id=str(body.id),
    )
    db.add(alert)
    await db.flush()

    run = AgentRun(alert_id=alert.id, status="running")
    db.add(run)
    await db.flush()

    alert_id = alert.id
    run_id = run.id
    await db.commit()

    asyncio.create_task(
        run_triage(
            run_id=run_id,
            alert_id=alert_id,
            device_id=body.device_id,
            alert_type=body.anomaly_type,
            severity_hint=_map_severity(body.severity),
            payload=payload,
        )
    )

    log.info(
        "SignalGuard anomaly %s accepted as alert %s (run %s)",
        body.id, alert_id, run_id,
    )
    return AlertSubmittedOut(alert_id=alert_id, run_id=run_id)
