"""Pydantic v2 request/response models for the HTTP API."""
from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field

Severity = Literal["low", "medium", "high", "critical"]
RiskLevel = Literal["low", "medium", "high"]


class AlertIn(BaseModel):
    device_id: str = Field(..., max_length=128)
    alert_type: str = Field(..., max_length=64)
    severity_hint: Severity | None = None
    payload: dict[str, Any] = Field(default_factory=dict)


class AlertOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    device_id: str
    alert_type: str
    severity_hint: str | None
    payload: dict[str, Any]
    created_at: datetime


class AlertSubmittedOut(BaseModel):
    alert_id: uuid.UUID
    run_id: uuid.UUID
    status: str = "running"


class AgentStepOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    step_index: int
    node_name: str
    status: str
    input_state: dict[str, Any] | None
    output_state: dict[str, Any] | None
    reasoning: str | None
    llm_calls: int
    tokens_used: int
    duration_ms: int
    error: str | None
    started_at: datetime


class AgentRunOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    alert_id: uuid.UUID
    status: str
    outcome: str | None
    summary: str | None
    severity: str | None
    failure_modes: list[str] | None
    retrieved_runbooks: list[dict[str, Any]] | None
    total_tokens: int
    total_llm_calls: int
    started_at: datetime
    completed_at: datetime | None
    steps: list[AgentStepOut] = Field(default_factory=list)


class RunbookOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    slug: str
    title: str
    risk_level: str
    indexed_at: datetime


class RunbookDetailOut(RunbookOut):
    content: str


# ─── Admin / LLM providers ────────────────────────────────────────────

ProviderName = Literal["openai", "anthropic", "gemini", "grok", "ollama"]


class ProviderCatalogEntry(BaseModel):
    name: ProviderName
    label: str
    models: list[str]
    needs_api_key: bool
    needs_base_url: bool


class ProviderStatus(BaseModel):
    name: ProviderName
    configured: bool
    is_active: bool
    api_key_last4: str | None
    active_model: str | None
    base_url: str | None


class ProviderUpdateIn(BaseModel):
    api_key: str | None = None
    base_url: str | None = None
    active_model: str | None = None


class ProviderActivateIn(BaseModel):
    name: ProviderName
    model: str


class ProviderTestIn(BaseModel):
    name: ProviderName
    api_key: str | None = None
    base_url: str | None = None
    model: str


class ProviderTestOut(BaseModel):
    success: bool
    message: str
    latency_ms: int | None = None
    tokens_used: int | None = None
