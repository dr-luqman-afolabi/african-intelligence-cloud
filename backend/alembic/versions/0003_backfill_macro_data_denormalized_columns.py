"""Backfill macro_data denormalized columns (country_iso3/indicator_code)

Revision ID: 0003
Revises: 0002
Create Date: 2026-07-04

Production's macro_data table predates Alembic and still has the original
schema (country_id/indicator_id FKs). The model/migration 0001 moved to a
denormalized schema (country_iso3/indicator_code strings + unit/source_id/
metadata) but 0001 never actually applied against prod (tables already
existed) and was papered over by a manual alembic stamp. This migration
reconciles prod with the model: it adds the new columns, backfills them
from the existing FKs via a join, and updates constraints/indexes. Nothing
is dropped - all legacy columns and rows are left intact.
"""
from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
from alembic import op

revision: str = "0003"
down_revision: Union[str, None] = "0002"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("macro_data", sa.Column("country_iso3", sa.String(3), nullable=True))
    op.add_column("macro_data", sa.Column("indicator_code", sa.String(255), nullable=True))
    op.add_column("macro_data", sa.Column("unit", sa.String(100), nullable=True))
    op.add_column("macro_data", sa.Column("source_id", sa.String(100), nullable=True))
    op.add_column("macro_data", sa.Column("metadata", postgresql.JSON(), nullable=True))
    op.alter_column("macro_data", "data_source", type_=sa.String(255), existing_type=sa.String(50))

    op.execute("UPDATE macro_data SET country_iso3 = c.iso3 FROM countries c WHERE macro_data.country_id = c.id")
    op.execute("UPDATE macro_data SET indicator_code = i.code FROM indicators i WHERE macro_data.indicator_id = i.id")

    op.alter_column("macro_data", "country_iso3", nullable=False)
    op.alter_column("macro_data", "indicator_code", nullable=False)

    op.create_index("ix_macro_data_country_iso3", "macro_data", ["country_iso3"])
    op.create_index("ix_macro_data_indicator_code", "macro_data", ["indicator_code"])
    op.create_index("ix_macro_data_source_id", "macro_data", ["source_id"])

    op.drop_constraint("uq_macro_data", "macro_data", type_="unique")
    op.create_unique_constraint("uq_macro_data", "macro_data", ["country_iso3", "indicator_code", "year"])
    op.create_index("ix_macro_data_country_indicator_year", "macro_data", ["country_iso3", "indicator_code", "year"])


def downgrade() -> None:
    op.drop_index("ix_macro_data_country_indicator_year", table_name="macro_data")
    op.drop_constraint("uq_macro_data", "macro_data", type_="unique")
    op.create_unique_constraint("uq_macro_data", "macro_data", ["country_id", "indicator_id", "year"])
    op.drop_index("ix_macro_data_source_id", table_name="macro_data")
    op.drop_index("ix_macro_data_indicator_code", table_name="macro_data")
    op.drop_index("ix_macro_data_country_iso3", table_name="macro_data")
    op.alter_column("macro_data", "data_source", type_=sa.String(50), existing_type=sa.String(255))
    op.drop_column("macro_data", "metadata")
    op.drop_column("macro_data", "source_id")
    op.drop_column("macro_data", "unit")
    op.drop_column("macro_data", "indicator_code")
    op.drop_column("macro_data", "country_iso3")
