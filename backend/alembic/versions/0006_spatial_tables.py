"""Spatial tables — Africa-wide GIS poverty mapping

Revision ID: 0006
Revises: 0005
Create Date: 2026-07-07

"""
from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
from alembic import op

revision: str = "0006"
down_revision: Union[str, None] = "0005"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()

    def has_table(name: str) -> bool:
        return name in sa.inspect(bind).get_table_names()

    if not has_table("spatial_units"):
        op.create_table(
            "spatial_units",
            sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
            sa.Column("country", sa.String(255), nullable=False),
            sa.Column("iso3", sa.String(3), nullable=False),
            sa.Column("admin_level", sa.String(10), nullable=False),
            sa.Column("admin_name", sa.String(500), nullable=False),
            sa.Column("admin_code", sa.String(100), nullable=True),
            sa.Column(
                "parent_unit_id", postgresql.UUID(as_uuid=True),
                sa.ForeignKey("spatial_units.id", ondelete="SET NULL"), nullable=True
            ),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        )
        op.create_index("ix_spatial_units_iso3_level", "spatial_units", ["iso3", "admin_level"])
        op.create_index("ix_spatial_units_iso3", "spatial_units", ["iso3"])

    if not has_table("spatial_boundaries"):
        op.create_table(
            "spatial_boundaries",
            sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
            sa.Column(
                "unit_id", postgresql.UUID(as_uuid=True),
                sa.ForeignKey("spatial_units.id", ondelete="CASCADE"), nullable=False
            ),
            sa.Column("source", sa.String(50), nullable=False),
            sa.Column("year", sa.Integer(), nullable=True),
            sa.Column("geometry", sa.JSON(), nullable=False),
            sa.Column("crs", sa.String(50), nullable=False, server_default="EPSG:4326"),
            sa.Column("license", sa.String(255), nullable=True),
            sa.Column("uploaded_by", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        )
        op.create_index("ix_spatial_boundaries_unit", "spatial_boundaries", ["unit_id"])


def downgrade() -> None:
    bind = op.get_bind()
    existing_tables = set(sa.inspect(bind).get_table_names())

    if "spatial_boundaries" in existing_tables:
        op.drop_table("spatial_boundaries")
    if "spatial_units" in existing_tables:
        op.drop_table("spatial_units")
