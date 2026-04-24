"""Escalation node — creates a human-review ticket row and stops the graph."""
from __future__ import annotations

import logging
import time
import uuid

from db.models import EscalationTicket
from db.session import session_scope
from services.audit_logger import record_step

from .state import TriageState

log = logging.getLogger("ranger.agents.escalation")


def _build_reason(state: TriageState) -> str:
    parts = []
    severity = state.get("severity")
    if severity in ("critical", "high"):
        parts.append(f"Severity={severity} — policy mandates human review.")
    if state.get("requires_human_context"):
        parts.append("Alert category (tamper / unauthorized / firmware / enrollment) is never auto-remediated.")
    if state.get("recommended_action") in ("escalate", "firmware_update"):
        parts.append(f"Knowledge agent recommended {state.get('recommended_action')}.")
    if state.get("remediation_attempts", 0) > 0 and not state.get("remediation_success"):
        parts.append(f"Auto-remediation failed after {state.get('remediation_attempts')} attempt(s).")
    if not parts:
        parts.append("Escalation requested by graph router.")
    return " ".join(parts)


async def escalation_node(state: TriageState) -> TriageState:
    run_id = uuid.UUID(state["run_id"])
    step_index = state.get("step_counter", 0)
    start = time.perf_counter()

    reason = _build_reason(state)
    severity = state.get("severity") or "medium"

    ticket_id = uuid.uuid4()
    async with session_scope() as session:
        session.add(
            EscalationTicket(
                id=ticket_id,
                run_id=run_id,
                reason=reason,
                severity=severity,
                status="open",
            )
        )

    duration_ms = int((time.perf_counter() - start) * 1000)

    await record_step(
        run_id,
        step_index,
        "escalate_node",
        status="done",
        input_state={
            "severity": severity,
            "recommended_action": state.get("recommended_action"),
            "remediation_success": state.get("remediation_success"),
        },
        output_state={"ticket_id": str(ticket_id), "reason": reason},
        reasoning=f"Created escalation ticket {ticket_id}. Reason: {reason}",
        duration_ms=duration_ms,
    )

    return {
        **state,
        "escalation_reason": reason,
        "escalation_ticket_id": str(ticket_id),
        "step_counter": step_index + 1,
    }
