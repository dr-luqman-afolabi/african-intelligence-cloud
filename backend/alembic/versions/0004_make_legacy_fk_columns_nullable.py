"""Make legacy FK columns nullable on macro_data

Revision ID: 0004
Revises: 0003
Create Date: 2026-07-04

Legacy country_id/indicator_id FK columns on macro_data are still NOT
NULL from the pre-Alembic schema. The app no longer populates them on
insert, so every new sync write fails with a NotNullViolation. This
relaxes them to nullable; nothing is dropped.
"""
from __future__ import annotations

from typing import Sequence, Union

from alembic import op

revision: str = "0004"
down_revision: Union[str, None] = "0003"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
  op.alter_column("macro_data", "country_id", nullable=True)
  op.alter_column("macro_data", "indicator_id", nullable=True)


def downgrade() -> None:
  op.alter_column("macro_data", "indicator_id", nullable=False)
  op.alter_column("macro_data", "country_id", nullable=False)
