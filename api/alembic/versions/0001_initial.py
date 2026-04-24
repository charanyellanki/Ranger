"""initial schema

Revision ID: 0001
Revises:
Create Date: 2026-04-24

"""
from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "alerts",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("device_id", sa.String(128), nullable=False),
        sa.Column("alert_type", sa.String(64), nullable=False),
        sa.Column("severity_hint", sa.String(16), nullable=True),
        sa.Column("payload", sa.JSON(), nullable=False, server_default="{}"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_alerts_device_id", "alerts", ["device_id"])
    op.create_index("ix_alerts_alert_type", "alerts", ["alert_type"])
    op.create_index("ix_alerts_created_at", "alerts", ["created_at"])

    op.create_table(
        "agent_runs",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("alert_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("alerts.id", ondelete="CASCADE"), nullable=False),
        sa.Column("status", sa.String(32), nullable=False, server_default="running"),
        sa.Column("outcome", sa.String(64), nullable=True),
        sa.Column("summary", sa.Text(), nullable=True),
        sa.Column("severity", sa.String(16), nullable=True),
        sa.Column("failure_modes", sa.JSON(), nullable=True),
        sa.Column("retrieved_runbooks", sa.JSON(), nullable=True),
        sa.Column("total_tokens", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("total_llm_calls", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_agent_runs_alert_id", "agent_runs", ["alert_id"])
    op.create_index("ix_agent_runs_status", "agent_runs", ["status"])

    op.create_table(
        "agent_steps",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("run_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("agent_runs.id", ondelete="CASCADE"), nullable=False),
        sa.Column("step_index", sa.Integer(), nullable=False),
        sa.Column("node_name", sa.String(64), nullable=False),
        sa.Column("status", sa.String(32), nullable=False, server_default="done"),
        sa.Column("input_state", sa.JSON(), nullable=True),
        sa.Column("output_state", sa.JSON(), nullable=True),
        sa.Column("reasoning", sa.Text(), nullable=True),
        sa.Column("llm_calls", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("tokens_used", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("duration_ms", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("error", sa.Text(), nullable=True),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_agent_steps_run_id", "agent_steps", ["run_id"])
    op.create_index("ix_agent_steps_node_name", "agent_steps", ["node_name"])
    op.create_index("ix_agent_steps_run_step", "agent_steps", ["run_id", "step_index"])

    op.create_table(
        "llm_providers",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("name", sa.String(32), nullable=False, unique=True),
        sa.Column("encrypted_api_key", sa.Text(), nullable=True),
        sa.Column("api_key_last4", sa.String(4), nullable=True),
        sa.Column("base_url", sa.String(256), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("active_model", sa.String(128), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("name", name="uq_provider_name"),
    )

    op.create_table(
        "runbooks",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("slug", sa.String(128), nullable=False, unique=True),
        sa.Column("title", sa.String(256), nullable=False),
        sa.Column("risk_level", sa.String(16), nullable=False, server_default="low"),
        sa.Column("indexed_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("source_path", sa.String(512), nullable=False),
    )
    op.create_index("ix_runbooks_slug", "runbooks", ["slug"])

    op.create_table(
        "escalation_tickets",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("run_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("agent_runs.id", ondelete="CASCADE"), nullable=False),
        sa.Column("reason", sa.Text(), nullable=False),
        sa.Column("severity", sa.String(16), nullable=False),
        sa.Column("status", sa.String(32), nullable=False, server_default="open"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_escalation_tickets_run_id", "escalation_tickets", ["run_id"])


def downgrade() -> None:
    op.drop_table("escalation_tickets")
    op.drop_table("runbooks")
    op.drop_table("llm_providers")
    op.drop_table("agent_steps")
    op.drop_table("agent_runs")
    op.drop_table("alerts")
