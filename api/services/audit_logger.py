"""Persists agent_steps + agent_runs. One entry per node transition.

Also broadcasts each step to the per-run WebSocket subscribers via the
stream module.
"""
from __future__ import annotations

import json
import logging
import uuid
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import select, update

from db.models import AgentRun, AgentStep
from db.session import session_scope
from services.stream import publish

log = logging.getLogger(__name__)


def _json_safe(value: Any) -> Any:
    """Coerce arbitrary state to JSON-serializable form."""
    try:
        json.dumps(value, default=str)
        return value
    except (TypeError, ValueError):
        return json.loads(json.dumps(value, default=str))


async def record_step(
    run_id: uuid.UUID,
    step_index: int,
    node_name: str,
    *,
    status: str = "done",
    input_state: dict[str, Any] | None = None,
    output_state: dict[str, Any] | None = None,
    reasoning: str | None = None,
    llm_calls: int = 0,
    tokens_used: int = 0,
    duration_ms: int = 0,
    error: str | None = None,
) -> None:
    async with session_scope() as session:
        step = AgentStep(
            run_id=run_id,
            step_index=step_index,
            node_name=node_name,
            status=status,
            input_state=_json_safe(input_state) if input_state else None,
            output_state=_json_safe(output_state) if output_state else None,
            reasoning=reasoning,
            llm_calls=llm_calls,
            tokens_used=tokens_used,
            duration_ms=duration_ms,
            error=error,
        )
        session.add(step)

        if llm_calls or tokens_used:
            await session.execute(
                update(AgentRun)
                .where(AgentRun.id == run_id)
                .values(
                    total_llm_calls=AgentRun.total_llm_calls + llm_calls,
                    total_tokens=AgentRun.total_tokens + tokens_used,
                )
            )

    await publish(
        run_id,
        {
            "type": "step",
            "step_index": step_index,
            "node_name": node_name,
            "status": status,
            "reasoning": reasoning,
            "tokens_used": tokens_used,
            "duration_ms": duration_ms,
            "error": error,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        },
    )


async def finalize_run(
    run_id: uuid.UUID,
    *,
    status: str,
    outcome: str,
    summary: str,
    severity: str | None,
    failure_modes: list[str] | None,
    retrieved_runbooks: list[dict[str, Any]] | None,
) -> None:
    async with session_scope() as session:
        await session.execute(
            update(AgentRun)
            .where(AgentRun.id == run_id)
            .values(
                status=status,
                outcome=outcome,
                summary=summary,
                severity=severity,
                failure_modes=failure_modes,
                retrieved_runbooks=_json_safe(retrieved_runbooks) if retrieved_runbooks else None,
                completed_at=datetime.now(timezone.utc),
            )
        )

    await publish(
        run_id,
        {
            "type": "run_complete",
            "status": status,
            "outcome": outcome,
            "summary": summary,
            "severity": severity,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        },
    )


async def mark_run_failed(run_id: uuid.UUID, error: str) -> None:
    async with session_scope() as session:
        await session.execute(
            update(AgentRun)
            .where(AgentRun.id == run_id)
            .values(
                status="failed",
                outcome="failed",
                summary=f"Run failed: {error}",
                completed_at=datetime.now(timezone.utc),
            )
        )
    await publish(
        run_id,
        {
            "type": "run_failed",
            "error": error,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        },
    )
