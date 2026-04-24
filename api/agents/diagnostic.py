"""Diagnostic agent — classifies severity and extracts failure modes from the alert."""
from __future__ import annotations

import json
import logging
import time
import uuid
from typing import Any

from llm.client import LLMNotConfiguredError, complete, safe_json_loads
from services.audit_logger import record_step

from .state import TriageState

log = logging.getLogger("ranger.agents.diagnostic")

SYSTEM_PROMPT = """You are the Diagnostic Agent in an IoT incident triage system.

Your job: given an alert, classify it and identify probable failure modes.

Output JSON only, matching this schema exactly:
{
  "severity": "low" | "medium" | "high" | "critical",
  "failure_modes": [ "...", "..." ],
  "summary": "one-paragraph plain-language explanation",
  "requires_human_context": true | false
}

Severity guidance:
- critical: safety, security, data integrity, or fleet-wide signal
- high:     regulated assets, gateways, cert/firmware, unauthorized access patterns
- medium:   cellular/mqtt/unresponsive hangs, calibration drift, battery drain
- low:      routine maintenance, wifi blips, clock drift

Set requires_human_context=true when the alert indicates tampering, unauthorized
access, enrollment, or firmware operations — anything where auto-remediation is
never appropriate. Otherwise false.

Respond ONLY with valid JSON. No prose, no markdown fences."""


def _user_prompt(state: TriageState) -> str:
    return (
        "Alert received:\n"
        f"  device_id:     {state.get('device_id')}\n"
        f"  alert_type:    {state.get('alert_type')}\n"
        f"  severity_hint: {state.get('severity_hint')}\n"
        f"  payload:       {json.dumps(state.get('payload', {}), default=str)}\n\n"
        "Classify this alert and return the JSON structure described."
    )


def _heuristic_fallback(state: TriageState) -> dict[str, Any]:
    """Used when the LLM fails or is not configured — keeps the graph functional
    for demos and tests. Real output should always come from the model."""
    alert_type = (state.get("alert_type") or "").lower()
    severity_hint = state.get("severity_hint") or "medium"

    critical_markers = ("tamper", "unauthorized", "firmware")
    high_markers = ("cert", "enrollment", "gateway")

    if any(m in alert_type for m in critical_markers):
        severity = "critical"
        requires_human = True
    elif any(m in alert_type for m in high_markers):
        severity = "high"
        requires_human = True
    else:
        severity = severity_hint if severity_hint in {"low", "medium", "high", "critical"} else "medium"
        requires_human = False

    return {
        "severity": severity,
        "failure_modes": [alert_type or "unknown"],
        "summary": f"Heuristic classification applied (LLM unavailable). alert_type={alert_type}.",
        "requires_human_context": requires_human,
    }


async def diagnostic_node(state: TriageState) -> TriageState:
    run_id = uuid.UUID(state["run_id"])
    step_index = state.get("step_counter", 0)
    start = time.perf_counter()

    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": _user_prompt(state)},
    ]

    llm_calls = 0
    tokens = 0
    reasoning_text = ""
    error: str | None = None

    try:
        result = await complete(messages, json_mode=True, max_tokens=512, temperature=0.1)
        llm_calls = 1
        tokens = result.tokens_used
        reasoning_text = result.text
        parsed = safe_json_loads(result.text)
        if parsed is None:
            raise ValueError("Diagnostic agent produced non-JSON response")
        classification = {
            "severity": parsed.get("severity", "medium"),
            "failure_modes": parsed.get("failure_modes") or [state.get("alert_type", "unknown")],
            "summary": parsed.get("summary", ""),
            "requires_human_context": bool(parsed.get("requires_human_context", False)),
        }
    except LLMNotConfiguredError as e:
        error = str(e)
        classification = _heuristic_fallback(state)
        reasoning_text = "LLM not configured — using heuristic classification."
    except Exception as e:
        error = f"{type(e).__name__}: {e}"
        log.exception("Diagnostic node failed, falling back to heuristic")
        classification = _heuristic_fallback(state)
        reasoning_text = reasoning_text or f"LLM call failed: {error}"

    duration_ms = int((time.perf_counter() - start) * 1000)
    updates = {
        "severity": classification["severity"],
        "failure_modes": classification["failure_modes"],
        "diagnostic_summary": classification["summary"],
        "requires_human_context": classification["requires_human_context"],
        "step_counter": step_index + 1,
    }

    await record_step(
        run_id,
        step_index,
        "diagnostic_agent",
        status="done" if error is None else ("done" if classification else "failed"),
        input_state={
            "alert_type": state.get("alert_type"),
            "severity_hint": state.get("severity_hint"),
            "payload": state.get("payload"),
        },
        output_state=classification,
        reasoning=reasoning_text,
        llm_calls=llm_calls,
        tokens_used=tokens,
        duration_ms=duration_ms,
        error=error,
    )

    return {**state, **updates}
