"""WebSocket endpoint — streams per-run agent events to subscribed clients.

Contract: the client connects to `/ws/runs/{run_id}` and receives a JSON
message for every step event. On connection, we flush any steps already
written to DB so the timeline fills in even if the client joined late.
"""
from __future__ import annotations

import asyncio
import logging
import uuid

from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from sqlalchemy import select

from db.models import AgentRun, AgentStep
from db.session import session_scope
from services.stream import subscribe, unsubscribe

log = logging.getLogger("ranger.routes.websocket")

router = APIRouter(tags=["websocket"])


async def _replay_existing(run_id: uuid.UUID, ws: WebSocket) -> bool:
    """Push every step that has already been written. Returns True if the
    run is already complete (so we should close)."""
    async with session_scope() as session:
        run_res = await session.execute(select(AgentRun).where(AgentRun.id == run_id))
        run = run_res.scalar_one_or_none()
        if run is None:
            return False
        step_res = await session.execute(
            select(AgentStep).where(AgentStep.run_id == run_id).order_by(AgentStep.step_index)
        )
        for step in step_res.scalars().all():
            await ws.send_json(
                {
                    "type": "step",
                    "step_index": step.step_index,
                    "node_name": step.node_name,
                    "status": step.status,
                    "reasoning": step.reasoning,
                    "tokens_used": step.tokens_used,
                    "duration_ms": step.duration_ms,
                    "error": step.error,
                    "replayed": True,
                    "timestamp": step.started_at.isoformat(),
                }
            )
        if run.status == "completed":
            await ws.send_json(
                {
                    "type": "run_complete",
                    "status": run.status,
                    "outcome": run.outcome,
                    "summary": run.summary,
                    "severity": run.severity,
                    "replayed": True,
                    "timestamp": (run.completed_at or run.started_at).isoformat(),
                }
            )
            return True
        if run.status == "failed":
            await ws.send_json(
                {
                    "type": "run_failed",
                    "error": run.summary or "run failed",
                    "replayed": True,
                    "timestamp": (run.completed_at or run.started_at).isoformat(),
                }
            )
            return True
    return False


@router.websocket("/ws/runs/{run_id}")
async def run_websocket(ws: WebSocket, run_id: uuid.UUID) -> None:
    await ws.accept()
    queue = await subscribe(run_id)
    try:
        already_done = await _replay_existing(run_id, ws)
        if already_done:
            await ws.close()
            return
        while True:
            try:
                event = await asyncio.wait_for(queue.get(), timeout=30.0)
            except asyncio.TimeoutError:
                # Keep-alive — most browsers / proxies drop idle websockets.
                await ws.send_json({"type": "ping"})
                continue
            await ws.send_json(event)
            if event.get("type") in {"run_complete", "run_failed"}:
                await ws.close()
                return
    except WebSocketDisconnect:
        pass
    finally:
        await unsubscribe(run_id, queue)
