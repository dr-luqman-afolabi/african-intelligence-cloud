"""Add persistent sync watermarks and schedules.

Revision ID: 0009
Revises: 0008
Create Date: 2026-07-31
"""
from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0009"
down_revision: Union[str, None] = "0008"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    inspector = sa.inspect(op.get_bind())
    tables = set(inspector.get_table_names())

    if "sync_watermarks" not in tables:
        op.create_table(
            "sync_watermarks",
            sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
            sa.Column("source_id", sa.String(), nullable=False),
            sa.Column("last_cursor", sa.Text(), nullable=True),
            sa.Column("last_synced_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("records_synced", sa.String(), nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
            sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
            sa.UniqueConstraint("source_id", name="uq_sync_watermarks_source_id"),
        )
        op.create_index("ix_sync_watermarks_source_id", "sync_watermarks", ["source_id"])

    if "sync_schedules" not in tables:
        op.create_table(
            "sync_schedules",
            sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
            sa.Column("source_id", sa.String(), nullable=False),
            sa.Column("cron_minute", sa.String(), nullable=True, server_default="0"),
            sa.Column("cron_hour", sa.String(), nullable=True, server_default="2"),
            sa.Column("cron_day", sa.String(), nullable=True, server_default="*"),
            sa.Column("cron_month", sa.String(), nullable=True, server_default="*"),
            sa.Column("cron_day_of_week", sa.String(), nullable=True, server_default="*"),
            sa.Column("enabled", sa.Boolean(), nullable=False, server_default=sa.true()),
            sa.Column("last_triggered_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("next_run_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
            sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
            sa.UniqueConstraint("source_id", name="uq_sync_schedules_source_id"),
        )
        op.create_index("ix_sync_schedules_source_id", "sync_schedules", ["source_id"])


def downgrade() -> None:
    tables = set(sa.inspect(op.get_bind()).get_table_names())
    if "sync_schedules" in tables:
        op.drop_index("ix_sync_schedules_source_id", table_name="sync_schedules")
        op.drop_table("sync_schedules")
    if "sync_watermarks" in tables:
        op.drop_index("ix_sync_watermarks_source_id", table_name="sync_watermarks")
        op.drop_table("sync_watermarks")
