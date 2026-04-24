"""Mock IoT device control API.

Simulates realistic device responses for the Remediation Agent to call against.
Device state is in-memory — resets on container restart, which is fine for demo.
"""
from __future__ import annotations

import asyncio
import random
import time
from datetime import datetime, timezone
from typing import Literal

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

app = FastAPI(title="Ranger Mock Device API", version="0.1.0")


class DeviceState(BaseModel):
    device_id: str
    online: bool = True
    firmware_version: str = "2.4.1"
    last_restart: datetime | None = None
    last_sync: datetime | None = None
    auth_reset_count: int = 0
    signal_strength_dbm: int = -62
    battery_percent: int = 87
    uptime_seconds: int = 3600


class ActionResult(BaseModel):
    device_id: str
    action: str
    success: bool
    message: str
    duration_ms: int
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


# In-memory device registry. Auto-populates on first access so any device_id works.
_devices: dict[str, DeviceState] = {}


def _get_or_create(device_id: str) -> DeviceState:
    if device_id not in _devices:
        _devices[device_id] = DeviceState(
            device_id=device_id,
            signal_strength_dbm=random.randint(-95, -55),
            battery_percent=random.randint(20, 100),
        )
    return _devices[device_id]


async def _simulate_latency(min_ms: int = 120, max_ms: int = 600) -> int:
    delay = random.randint(min_ms, max_ms)
    await asyncio.sleep(delay / 1000)
    return delay


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/devices/{device_id}/status", response_model=DeviceState)
async def device_status(device_id: str) -> DeviceState:
    device = _get_or_create(device_id)
    # Drift the uptime so repeated calls look live.
    device.uptime_seconds += random.randint(1, 10)
    return device


@app.post("/devices/{device_id}/restart", response_model=ActionResult)
async def restart_device(device_id: str) -> ActionResult:
    device = _get_or_create(device_id)
    duration = await _simulate_latency(800, 2400)
    # 92% success rate.
    success = random.random() < 0.92
    if success:
        device.online = True
        device.last_restart = datetime.now(timezone.utc)
        device.uptime_seconds = 0
        device.signal_strength_dbm = min(-55, device.signal_strength_dbm + random.randint(3, 10))
        msg = f"Device {device_id} restarted successfully"
    else:
        device.online = False
        msg = f"Device {device_id} did not come back online within timeout"
    return ActionResult(
        device_id=device_id, action="restart", success=success, message=msg, duration_ms=duration
    )


@app.post("/devices/{device_id}/sync", response_model=ActionResult)
async def sync_device(device_id: str) -> ActionResult:
    device = _get_or_create(device_id)
    duration = await _simulate_latency(200, 900)
    success = random.random() < 0.96
    if success:
        device.last_sync = datetime.now(timezone.utc)
        msg = f"Device {device_id} synchronized with control plane"
    else:
        msg = f"Sync failed for {device_id}: control plane unreachable"
    return ActionResult(
        device_id=device_id, action="sync", success=success, message=msg, duration_ms=duration
    )


@app.post("/devices/{device_id}/reset_auth", response_model=ActionResult)
async def reset_auth(device_id: str) -> ActionResult:
    device = _get_or_create(device_id)
    duration = await _simulate_latency(400, 1200)
    success = random.random() < 0.88
    if success:
        device.auth_reset_count += 1
        msg = f"Auth credentials rotated for {device_id}"
    else:
        msg = f"Auth reset failed for {device_id}: provisioning service returned 503"
    return ActionResult(
        device_id=device_id,
        action="reset_auth",
        success=success,
        message=msg,
        duration_ms=duration,
    )


class FirmwareUpdateRequest(BaseModel):
    target_version: str


@app.post("/devices/{device_id}/firmware_update", response_model=ActionResult)
async def firmware_update(device_id: str, req: FirmwareUpdateRequest) -> ActionResult:
    """Destructive action — included so the agent router can correctly escalate it."""
    device = _get_or_create(device_id)
    duration = await _simulate_latency(2000, 5000)
    success = random.random() < 0.75
    if success:
        device.firmware_version = req.target_version
        msg = f"Firmware updated to {req.target_version}"
    else:
        device.online = False
        msg = f"Firmware update to {req.target_version} failed — device in recovery mode"
    return ActionResult(
        device_id=device_id,
        action="firmware_update",
        success=success,
        message=msg,
        duration_ms=duration,
    )


@app.get("/devices")
async def list_devices() -> dict[str, list[DeviceState]]:
    return {"devices": list(_devices.values())}
