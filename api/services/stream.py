"""In-process pub/sub for streaming agent events to WebSocket subscribers.

Single-instance by design — documented limitation for v1. See README "Future Work"
for the Redis/PostgresSaver path when we need multi-replica support.
"""
from __future__ import annotations

import asyncio
import logging
import uuid
from typing import Any

log = logging.getLogger(__name__)

_subscribers: dict[uuid.UUID, set[asyncio.Queue[dict[str, Any]]]] = {}
_lock = asyncio.Lock()


async def subscribe(run_id: uuid.UUID) -> asyncio.Queue[dict[str, Any]]:
    queue: asyncio.Queue[dict[str, Any]] = asyncio.Queue(maxsize=256)
    async with _lock:
        _subscribers.setdefault(run_id, set()).add(queue)
    return queue


async def unsubscribe(run_id: uuid.UUID, queue: asyncio.Queue[dict[str, Any]]) -> None:
    async with _lock:
        if run_id in _subscribers:
            _subscribers[run_id].discard(queue)
            if not _subscribers[run_id]:
                _subscribers.pop(run_id, None)


async def publish(run_id: uuid.UUID, event: dict[str, Any]) -> None:
    async with _lock:
        queues = list(_subscribers.get(run_id, ()))
    for q in queues:
        try:
            q.put_nowait(event)
        except asyncio.QueueFull:
            log.warning("Dropping event for run %s — subscriber queue full", run_id)
