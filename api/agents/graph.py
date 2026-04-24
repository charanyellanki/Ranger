"""LangGraph state machine wiring.

Flow:
  START → diagnostic_agent → knowledge_agent → router
    router → escalate_node           (critical|high|human-context|destructive)
    router → remediation_agent       (otherwise)
    remediation_agent → (success) → finalize → END
    remediation_agent → (failure) → escalate_node → finalize → END
    escalate_node → finalize → END
"""
from __future__ import annotations

import logging
import uuid
from typing import Literal

from langgraph.graph import END, START, StateGraph

from services.audit_logger import finalize_run, mark_run_failed

from .diagnostic import diagnostic_node
from .escalation import escalation_node
from .knowledge import knowledge_node
from .remediation import remediation_node
from .state import TriageState, initial_state

log = logging.getLogger("ranger.agents.graph")


DESTRUCTIVE_ACTIONS = {"firmware_update", "reset_auth"}


def _route_after_knowledge(state: TriageState) -> Literal["remediation_agent", "escalate_node"]:
    severity = state.get("severity", "medium")
    action = state.get("recommended_action", "escalate")

    if severity in ("critical", "high"):
        return "escalate_node"
    if state.get("requires_human_context"):
        return "escalate_node"
    if action in DESTRUCTIVE_ACTIONS or action == "escalate":
        return "escalate_node"
    return "remediation_agent"


def _route_after_remediation(state: TriageState) -> Literal["escalate_node", "finalize_success"]:
    if state.get("remediation_success"):
        return "finalize_success"
    return "escalate_node"


async def _finalize_success(state: TriageState) -> TriageState:
    run_id = uuid.UUID(state["run_id"])
    action = state.get("recommended_action", "unknown")
    summary = (
        f"Auto-remediated via `{action}` after {state.get('remediation_attempts', 0)} attempt(s). "
        f"{state.get('knowledge_summary', '')}"
    ).strip()
    await finalize_run(
        run_id,
        status="completed",
        outcome="remediated",
        summary=summary,
        severity=state.get("severity"),
        failure_modes=state.get("failure_modes"),
        retrieved_runbooks=state.get("retrieved_runbooks"),
    )
    return {**state, "outcome": "remediated", "summary": summary}


async def _finalize_escalated(state: TriageState) -> TriageState:
    run_id = uuid.UUID(state["run_id"])
    summary = (
        f"Escalated to human review. Reason: {state.get('escalation_reason', 'unspecified')}. "
        f"{state.get('knowledge_summary', '')}"
    ).strip()
    await finalize_run(
        run_id,
        status="completed",
        outcome="escalated",
        summary=summary,
        severity=state.get("severity"),
        failure_modes=state.get("failure_modes"),
        retrieved_runbooks=state.get("retrieved_runbooks"),
    )
    return {**state, "outcome": "escalated", "summary": summary}


def build_graph():
    graph = StateGraph(TriageState)

    graph.add_node("diagnostic_agent", diagnostic_node)
    graph.add_node("knowledge_agent", knowledge_node)
    graph.add_node("remediation_agent", remediation_node)
    graph.add_node("escalate_node", escalation_node)
    graph.add_node("finalize_success", _finalize_success)
    graph.add_node("finalize_escalated", _finalize_escalated)

    graph.add_edge(START, "diagnostic_agent")
    graph.add_edge("diagnostic_agent", "knowledge_agent")

    graph.add_conditional_edges(
        "knowledge_agent",
        _route_after_knowledge,
        {
            "remediation_agent": "remediation_agent",
            "escalate_node": "escalate_node",
        },
    )

    graph.add_conditional_edges(
        "remediation_agent",
        _route_after_remediation,
        {
            "finalize_success": "finalize_success",
            "escalate_node": "escalate_node",
        },
    )

    graph.add_edge("escalate_node", "finalize_escalated")
    graph.add_edge("finalize_success", END)
    graph.add_edge("finalize_escalated", END)

    return graph.compile()


async def run_triage(
    *,
    run_id: uuid.UUID,
    alert_id: uuid.UUID,
    device_id: str,
    alert_type: str,
    severity_hint: str | None,
    payload: dict,
) -> None:
    """Top-level entrypoint used by the /alerts route as a background task."""
    graph = build_graph()
    state = initial_state(
        run_id=run_id,
        alert_id=alert_id,
        device_id=device_id,
        alert_type=alert_type,
        severity_hint=severity_hint,
        payload=payload,
    )
    try:
        await graph.ainvoke(state)
    except Exception as e:
        log.exception("Triage run %s failed", run_id)
        await mark_run_failed(run_id, f"{type(e).__name__}: {e}")
