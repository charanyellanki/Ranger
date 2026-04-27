"""Ranger API entrypoint."""
from __future__ import annotations

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from config import get_settings
from routes import agent_runs, alerts, runbooks, settings, webhooks, websocket

_settings = get_settings()
logging.basicConfig(level=_settings.log_level, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
log = logging.getLogger("ranger.api")


@asynccontextmanager
async def lifespan(app: FastAPI):
    log.info("Ranger API starting — active CORS origins: %s", _settings.cors_origin_list)
    yield
    log.info("Ranger API shutting down")


app = FastAPI(
    title="Ranger API",
    description="Multi-agent IoT incident triage",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=_settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}


app.include_router(alerts.router)
app.include_router(agent_runs.router)
app.include_router(runbooks.router)
app.include_router(settings.router)
app.include_router(webhooks.router)
app.include_router(websocket.router)
