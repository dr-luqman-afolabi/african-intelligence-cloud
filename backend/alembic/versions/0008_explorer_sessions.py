"""Interactive spatial-explorer sessions — saved/replayable exploration state

Revision ID: 0008
Revises: 0007
Create Date: 2026-07-09

"""
from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
from alembic import op

revision: str = "0008"
down_revision: Union[str, None] = "0007"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()

    def has_table(name: str) -> bool:
        return name in sa.inspect(bind).get_table_names()

    if not has_table("microdata_explorer_sessions"):
        op.create_table(
            "microdata_explorer_sessions",
            sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
            sa.Column("name", sa.String(255), nullable=False, server_default="Untitled exploration"),
            sa.Column("owner_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=False),
            sa.Column(
                "dataset_id", postgresql.UUID(as_uuid=True),
                sa.ForeignKey("microdata_datasets.id", ondelete="SET NULL"), nullable=True,
            ),
            sa.Column("country_iso3", sa.String(3), nullable=True),
            sa.Column("admin_level", sa.String(10), nullable=True),
            sa.Column("active_layer", sa.String(30), nullable=False, server_default="poverty"),
            sa.Column("state", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
            sa.Column(
                "last_result_job_id", postgresql.UUID(as_uuid=True),
                sa.ForeignKey("microdata_analysis_jobs.id", ondelete="SET NULL"), nullable=True,
            ),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
            sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        )
        op.create_index(
            "ix_microdata_explorer_sessions_owner",
            "microdata_explorer_sessions", ["owner_id"],
        )


def downgrade() -> None:
    bind = op.get_bind()
    if "microdata_explorer_sessions" in sa.inspect(bind).get_table_names():
        op.drop_index("ix_microdata_explorer_sessions_owner", table_name="microdata_explorer_sessions")
        op.drop_table("microdata_explorer_sessions")
