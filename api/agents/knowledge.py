"""Knowledge agent — retrieves runbooks via RAG, synthesizes recommendation."""
from __future__ import annotations

import json
import logging
import time
import uuid

from llm.client import LLMNotConfiguredError, complete, safe_json_loads
from rag.retriever import retrieve
from services.audit_logger import record_step

from .state import TriageState

log = logging.getLogger("ranger.agents.knowledge")

SYSTEM_PROMPT = """You are the Knowledge Agent in an IoT incident triage system.

Inputs:
  - Diagnosis from the Diagnostic Agent (severity + failure modes)
  - The top runbook excerpts retrieved via RAG

Your job: read the excerpts and recommend ONE of:
  - "sync"         — safe low-risk re-sync of device configuration
  - "restart"      — safe but heavier, resets device state
  - "reset_auth"   — rotates credentials; medium risk, often requires escalation
  - "escalate"    — the correct action per runbooks is human review
  - "firmware_update" — destructive, ALWAYS pair with escalation

Also produce a risk classification for the recommended action:
  "low" | "medium" | "high"

Output JSON only:
{
  "recommended_action": "sync|restart|reset_auth|escalate|firmware_update",
  "action_risk_level":  "low|medium|high",
  "summary": "2-3 sentence plain-language explanation citing the runbook(s)"
}

Rules:
- If ANY retrieved runbook instructs "always escalate" for this failure mode, recommend "escalate".
- Prefer the least-invasive action that the runbooks support.
- Do not invent actions not listed above.
"""


def _format_runbooks_for_prompt(runbooks: list[dict]) -> str:
    if not runbooks:
        return "(No runbooks retrieved.)"
    parts = []
    for i, rb in enumerate(runbooks, start=1):
        parts.append(
            f"[{i}] {rb.get('title')} (risk_level={rb.get('risk_level')}, score={rb.get('score')})\n"
            f"{rb.get('excerpt', '')}"
        )
    return "\n\n".join(parts)


def _query_for_failure(state: TriageState) -> str:
    modes = state.get("failure_modes") or [state.get("alert_type", "")]
    summary = state.get("diagnostic_summary") or ""
    return f"IoT device issue: {', '.join(modes)}. Context: {summary}"


def _heuristic_recommendation(state: TriageState, runbooks: list[dict]) -> dict:
    if state.get("requires_human_context"):
        return {
            "recommended_action": "escalate",
            "action_risk_level": "high",
            "summary": "Alert category requires human review (fallback path).",
        }
    severity = state.get("severity", "medium")
    if severity in ("critical", "high"):
        return {
            "recommended_action": "escalate",
            "action_risk_level": "high",
            "summary": f"Severity is {severity} — escalation is the safe default without LLM guidance.",
        }
    # Most low/medium device faults respond to sync-then-restart. Default to sync.
    return {
        "recommended_action": "sync",
        "action_risk_level": "low",
        "summary": "Heuristic fallback — attempt sync as the least-invasive first step.",
    }


async def knowledge_node(state: TriageState) -> TriageState:
    run_id = uuid.UUID(state["run_id"])
    step_index = state.get("step_counter", 0)
    start = time.perf_counter()

    query = _query_for_failure(state)
    try:
        runbooks = await retrieve(query, top_k=3)
    except Exception as e:
        log.exception("RAG retrieval failed")
        runbooks = []

    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {
            "role": "user",
            "content": (
                f"Diagnosis:\n  severity: {state.get('severity')}\n"
                f"  failure_modes: {state.get('failure_modes')}\n"
                f"  summary: {state.get('diagnostic_summary')}\n\n"
                f"Retrieved runbooks:\n{_format_runbooks_for_prompt(runbooks)}\n\n"
                "Return the JSON recommendation."
            ),
        },
    ]

    llm_calls = 0
    tokens = 0
    reasoning_text = ""
    error: str | None = None

    try:
        result = await complete(messages, json_mode=True, max_tokens=512, temperature=0.2)
        llm_calls = 1
        tokens = result.tokens_used
        reasoning_text = result.text
        parsed = safe_json_loads(result.text)
        if parsed is None:
            raise ValueError("Knowledge agent produced non-JSON response")
        recommendation = {
            "recommended_action": parsed.get("recommended_action", "escalate"),
            "action_risk_level": parsed.get("action_risk_level", "medium"),
            "summary": parsed.get("summary", ""),
        }
    except LLMNotConfiguredError as e:
        error = str(e)
        recommendation = _heuristic_recommendation(state, runbooks)
        reasoning_text = "LLM not configured — using heuristic recommendation."
    except Exception as e:
        error = f"{type(e).__name__}: {e}"
        log.exception("Knowledge node LLM call failed")
        recommendation = _heuristic_recommendation(state, runbooks)
        reasoning_text = reasoning_text or f"LLM call failed: {error}"

    duration_ms = int((time.perf_counter() - start) * 1000)
    updates = {
        "retrieved_runbooks": runbooks,
        "recommended_action": recommendation["recommended_action"],
        "action_risk_level": recommendation["action_risk_level"],
        "knowledge_summary": recommendation["summary"],
        "step_counter": step_index + 1,
    }

    await record_step(
        run_id,
        step_index,
        "knowledge_agent",
        status="done",
        input_state={
            "query": query,
            "top_k": 3,
            "severity": state.get("severity"),
            "failure_modes": state.get("failure_modes"),
        },
        output_state={
            "retrieved_runbooks": [
                {k: v for k, v in rb.items() if k != "excerpt"} for rb in runbooks
            ],
            **recommendation,
        },
        reasoning=reasoning_text,
        llm_calls=llm_calls,
        tokens_used=tokens,
        duration_ms=duration_ms,
        error=error,
    )

    return {**state, **updates}
