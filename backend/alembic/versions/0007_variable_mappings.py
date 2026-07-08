"""Variable mappings — LSMS standard-concept mapping engine

Revision ID: 0007
Revises: 0006
Create Date: 2026-07-07

"""
from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
from alembic import op

revision: str = "0007"
down_revision: Union[str, None] = "0006"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()

    def has_table(name: str) -> bool:
        return name in sa.inspect(bind).get_table_names()

    if not has_table("variable_mappings"):
        op.create_table(
            "variable_mappings",
            sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
            sa.Column(
                "dataset_id", postgresql.UUID(as_uuid=True),
                sa.ForeignKey("microdata_datasets.id"), nullable=False
            ),
            sa.Column("standard_concept", sa.String(50), nullable=False),
            sa.Column("raw_variable_name", sa.String(255), nullable=False),
            sa.Column("confidence", sa.Integer(), nullable=True),
            sa.Column("auto_detected", sa.Boolean(), nullable=False, server_default=sa.false()),
            sa.Column("created_by", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
            sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        )
        op.create_index("ix_variable_mappings_dataset", "variable_mappings", ["dataset_id"])
        op.create_index(
            "ix_variable_mappings_dataset_concept", "variable_mappings",
            ["dataset_id", "standard_concept"], unique=True,
        )


def downgrade() -> None:
    bind = op.get_bind()
    if "variable_mappings" in set(sa.inspect(bind).get_table_names()):
        op.drop_table("variable_mappings")
