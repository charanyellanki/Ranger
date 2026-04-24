"""Shared state for the LangGraph triage graph.

TypedDict shape is what LangGraph expects. Kept flat and JSON-serializable
so `input_state` / `output_state` audit columns round-trip cleanly.
"""
from __future__ import annotations

import uuid
from typing import Any, Literal, TypedDict

Severity = Literal["low", "medium", "high", "critical"]


class TriageState(TypedDict, total=False):
    # ─── Identifiers ────────────────────────────────────────────────
    run_id: str
    alert_id: str
    step_counter: int  # monotonically increasing step index for audit

    # ─── Input ──────────────────────────────────────────────────────
    device_id: str
    alert_type: str
    severity_hint: str | None
    payload: dict[str, Any]

    # ─── Diagnostic agent output ────────────────────────────────────
    severity: Severity
    failure_modes: list[str]
    diagnostic_summary: str
    requires_human_context: bool

    # ─── Knowledge agent output ─────────────────────────────────────
    retrieved_runbooks: list[dict[str, Any]]
    recommended_action: str  # e.g. "restart", "sync", "reset_auth", "escalate"
    action_risk_level: str  # "low" | "medium" | "high"
    knowledge_summary: str

    # ─── Remediation output ─────────────────────────────────────────
    remediation_attempts: int
    remediation_success: bool
    remediation_results: list[dict[str, Any]]

    # ─── Escalation output ──────────────────────────────────────────
    escalation_reason: str | None
    escalation_ticket_id: str | None

    # ─── Final outcome ──────────────────────────────────────────────
    outcome: str  # "remediated" | "escalated" | "failed"
    summary: str


def initial_state(
    *,
    run_id: uuid.UUID,
    alert_id: uuid.UUID,
    device_id: str,
    alert_type: str,
    severity_hint: str | None,
    payload: dict[str, Any],
) -> TriageState:
    return TriageState(
        run_id=str(run_id),
        alert_id=str(alert_id),
        step_counter=0,
        device_id=device_id,
        alert_type=alert_type,
        severity_hint=severity_hint,
        payload=payload,
        remediation_attempts=0,
        remediation_success=False,
        remediation_results=[],
    )
