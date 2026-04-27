"""add alert source fields

Revision ID: 0002
Revises: 0001
Create Date: 2026-04-26

"""
from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0002"
down_revision: Union[str, None] = "0001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("alerts", sa.Column("source", sa.String(32), nullable=True))
    op.add_column("alerts", sa.Column("source_id", sa.String(64), nullable=True))
    op.create_index("ix_alerts_source", "alerts", ["source"])


def downgrade() -> None:
    op.drop_index("ix_alerts_source", table_name="alerts")
    op.drop_column("alerts", "source_id")
    op.drop_column("alerts", "source")
