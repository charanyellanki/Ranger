"""Remediation agent — executes the recommended device action via mock-device-api."""
from __future__ import annotations

import logging
import time
import uuid

import httpx

from config import get_settings
from services.audit_logger import record_step

from .state import TriageState

log = logging.getLogger("ranger.agents.remediation")

MAX_ATTEMPTS = 3

_ENDPOINTS = {
    "sync": "/devices/{device_id}/sync",
    "restart": "/devices/{device_id}/restart",
    "reset_auth": "/devices/{device_id}/reset_auth",
}


async def _call_device_action(action: str, device_id: str) -> dict:
    endpoint = _ENDPOINTS[action].format(device_id=device_id)
    url = f"{get_settings().mock_device_api_url}{endpoint}"
    async with httpx.AsyncClient(timeout=15.0) as client:
        resp = await client.post(url)
        resp.raise_for_status()
        return resp.json()


async def remediation_node(state: TriageState) -> TriageState:
    run_id = uuid.UUID(state["run_id"])
    step_index = state.get("step_counter", 0)
    start = time.perf_counter()

    action = state.get("recommended_action", "sync")
    device_id = state["device_id"]

    if action not in _ENDPOINTS:
        # Action isn't auto-remediable (escalate / firmware_update). Pass through
        # without calling the device — the router will hand off to escalate.
        duration_ms = int((time.perf_counter() - start) * 1000)
        await record_step(
            run_id,
            step_index,
            "remediation_agent",
            status="done",
            input_state={"recommended_action": action},
            output_state={"skipped": True, "reason": "Action is not auto-remediable"},
            reasoning=f"Skipping auto-remediation: '{action}' is not in the auto-remediable set.",
            duration_ms=duration_ms,
        )
        return {
            **state,
            "remediation_success": False,
            "step_counter": step_index + 1,
        }

    attempts: list[dict] = list(state.get("remediation_results") or [])
    success = False
    reasoning_lines: list[str] = []
    error: str | None = None

    for attempt_num in range(1, MAX_ATTEMPTS + 1):
        try:
            response = await _call_device_action(action, device_id)
            attempt_success = bool(response.get("success"))
            attempts.append(
                {
                    "attempt": attempt_num,
                    "action": action,
                    "device_id": device_id,
                    "success": attempt_success,
                    "message": response.get("message"),
                    "duration_ms": response.get("duration_ms"),
                }
            )
            reasoning_lines.append(
                f"Attempt {attempt_num}: {action} → {'OK' if attempt_success else 'FAILED'} "
                f"({response.get('message', '')})"
            )
            if attempt_success:
                success = True
                break
        except httpx.HTTPError as e:
            err = f"Attempt {attempt_num}: HTTP error {type(e).__name__}: {e}"
            reasoning_lines.append(err)
            attempts.append(
                {
                    "attempt": attempt_num,
                    "action": action,
                    "device_id": device_id,
                    "success": False,
                    "message": str(e),
                }
            )
            error = err

    duration_ms = int((time.perf_counter() - start) * 1000)

    await record_step(
        run_id,
        step_index,
        "remediation_agent",
        status="done" if success else "failed",
        input_state={"action": action, "device_id": device_id, "max_attempts": MAX_ATTEMPTS},
        output_state={"success": success, "attempts": attempts},
        reasoning="\n".join(reasoning_lines),
        duration_ms=duration_ms,
        error=None if success else error,
    )

    return {
        **state,
        "remediation_attempts": len(attempts),
        "remediation_success": success,
        "remediation_results": attempts,
        "step_counter": step_index + 1,
    }
