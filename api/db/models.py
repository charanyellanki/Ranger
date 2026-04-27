"""SQLAlchemy models.

Schema mirrors the audit story in the README: alerts trigger agent_runs,
each run has an ordered list of agent_steps. LLM providers are stored with
Fernet-encrypted keys.
"""
from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import JSON, ForeignKey, Index, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class Base(DeclarativeBase):
    pass


class Alert(Base):
    __tablename__ = "alerts"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    device_id: Mapped[str] = mapped_column(String(128), index=True)
    alert_type: Mapped[str] = mapped_column(String(64), index=True)
    severity_hint: Mapped[str | None] = mapped_column(String(16), nullable=True)
    payload: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(default=utcnow, index=True)

    # Upstream source tracking (e.g. "signalguard")
    source: Mapped[str | None] = mapped_column(String(32), nullable=True, index=True)
    source_id: Mapped[str | None] = mapped_column(String(64), nullable=True)

    runs: Mapped[list["AgentRun"]] = relationship(
        back_populates="alert", cascade="all, delete-orphan"
    )


class AgentRun(Base):
    __tablename__ = "agent_runs"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    alert_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("alerts.id", ondelete="CASCADE"), index=True
    )
    status: Mapped[str] = mapped_column(String(32), default="running", index=True)
    # running | remediated | escalated | failed
    outcome: Mapped[str | None] = mapped_column(String(64), nullable=True)
    summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    severity: Mapped[str | None] = mapped_column(String(16), nullable=True)
    failure_modes: Mapped[list[str] | None] = mapped_column(JSON, nullable=True)
    retrieved_runbooks: Mapped[list[dict[str, Any]] | None] = mapped_column(JSON, nullable=True)
    total_tokens: Mapped[int] = mapped_column(default=0)
    total_llm_calls: Mapped[int] = mapped_column(default=0)
    started_at: Mapped[datetime] = mapped_column(default=utcnow)
    completed_at: Mapped[datetime | None] = mapped_column(nullable=True)

    alert: Mapped[Alert] = relationship(back_populates="runs")
    steps: Mapped[list["AgentStep"]] = relationship(
        back_populates="run", cascade="all, delete-orphan", order_by="AgentStep.step_index"
    )


class AgentStep(Base):
    """Immutable audit row — one per node transition inside a graph run."""

    __tablename__ = "agent_steps"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    run_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("agent_runs.id", ondelete="CASCADE"), index=True
    )
    step_index: Mapped[int] = mapped_column()
    node_name: Mapped[str] = mapped_column(String(64), index=True)
    status: Mapped[str] = mapped_column(String(32), default="done")
    # pending | running | done | failed
    input_state: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)
    output_state: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)
    reasoning: Mapped[str | None] = mapped_column(Text, nullable=True)
    llm_calls: Mapped[int] = mapped_column(default=0)
    tokens_used: Mapped[int] = mapped_column(default=0)
    duration_ms: Mapped[int] = mapped_column(default=0)
    error: Mapped[str | None] = mapped_column(Text, nullable=True)
    started_at: Mapped[datetime] = mapped_column(default=utcnow)

    run: Mapped[AgentRun] = relationship(back_populates="steps")

    __table_args__ = (
        Index("ix_agent_steps_run_step", "run_id", "step_index"),
    )


class LLMProvider(Base):
    __tablename__ = "llm_providers"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(32), unique=True)  # openai|anthropic|gemini|grok|ollama
    encrypted_api_key: Mapped[str | None] = mapped_column(Text, nullable=True)
    api_key_last4: Mapped[str | None] = mapped_column(String(4), nullable=True)
    base_url: Mapped[str | None] = mapped_column(String(256), nullable=True)  # for ollama
    is_active: Mapped[bool] = mapped_column(default=False)
    active_model: Mapped[str | None] = mapped_column(String(128), nullable=True)
    updated_at: Mapped[datetime] = mapped_column(default=utcnow, onupdate=utcnow)

    __table_args__ = (UniqueConstraint("name", name="uq_provider_name"),)


class Runbook(Base):
    """Metadata only. Content + embeddings live in ChromaDB."""

    __tablename__ = "runbooks"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    slug: Mapped[str] = mapped_column(String(128), unique=True, index=True)
    title: Mapped[str] = mapped_column(String(256))
    risk_level: Mapped[str] = mapped_column(String(16), default="low")
    indexed_at: Mapped[datetime] = mapped_column(default=utcnow)
    source_path: Mapped[str] = mapped_column(String(512))


class EscalationTicket(Base):
    __tablename__ = "escalation_tickets"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    run_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("agent_runs.id", ondelete="CASCADE"), index=True
    )
    reason: Mapped[str] = mapped_column(Text)
    severity: Mapped[str] = mapped_column(String(16))
    status: Mapped[str] = mapped_column(String(32), default="open")  # open | acknowledged | resolved
    created_at: Mapped[datetime] = mapped_column(default=utcnow)
