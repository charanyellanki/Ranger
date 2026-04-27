"""Callback to SignalGuard after triage completes.

When Ranger finishes triaging an alert that originated from SignalGuard, we
POST back to SignalGuard's ``/anomalies/{id}/action`` to close the loop.
"""
from __future__ import annotations

import logging
import uuid

import httpx
from sqlalchemy import select

from config import get_settings
from db.models import Alert
from db.session import session_scope

log = logging.getLogger("ranger.services.signalguard_callback")


async def notify_signalguard(
    alert_id: uuid.UUID,
    outcome: str,
    summary: str,
) -> None:
    """If the alert came from SignalGuard, update the anomaly status there.

    - ``outcome == "remediated"`` → action ``resolve``
    - ``outcome == "escalated"``  → action ``acknowledge`` (human still needed)
    - anything else               → no-op
    """
    settings = get_settings()
    if not settings.signalguard_api_url:
        return

    async with session_scope() as session:
        result = await session.execute(
            select(Alert.source, Alert.source_id).where(Alert.id == alert_id)
        )
        row = result.one_or_none()

    if row is None or row.source != "signalguard" or not row.source_id:
        return

    action_map = {
        "remediated": "resolve",
        "escalated": "acknowledge",
    }
    action = action_map.get(outcome)
    if action is None:
        return

    url = f"{settings.signalguard_api_url.rstrip('/')}/anomalies/{row.source_id}/action"
    body = {
        "action": action,
        "assignee": "ranger-bot",
        "note": summary[:500],
    }

    try:
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.post(url, json=body)
            resp.raise_for_status()
        log.info(
            "Notified SignalGuard anomaly %s → %s",
            row.source_id, action,
        )
    except Exception:
        log.exception("Failed to callback SignalGuard for anomaly %s", row.source_id)
