"""Microdata tables — Poverty & Microdata Analytics Studio

Revision ID: 0005
Revises: 0004
Create Date: 2026-07-06

"""
from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
from alembic import op


revision: str = "0005"
down_revision: Union[str, None] = "0004"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "microdata_projects",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("country_iso3", sa.String(3), nullable=True),
        sa.Column("owner_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("organization_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("organizations.id"), nullable=True),
        sa.Column("access_status", sa.String(50), nullable=False, server_default="user_upload"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    op.create_table(
        "microdata_datasets",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("project_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("microdata_projects.id"), nullable=True),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("original_filename", sa.String(500), nullable=False),
        sa.Column("file_type", sa.String(20), nullable=False),
        sa.Column("storage_path", sa.String(1000), nullable=False),
        sa.Column("file_size_bytes", sa.BigInteger(), nullable=True),
        sa.Column("country_iso3", sa.String(3), nullable=True),
        sa.Column("survey_series", sa.String(100), nullable=True),
        sa.Column("year", sa.Integer(), nullable=True),
        sa.Column("row_count", sa.Integer(), nullable=True),
        sa.Column("column_count", sa.Integer(), nullable=True),
        sa.Column("missing_cells", sa.Integer(), nullable=True),
        sa.Column("access_status", sa.String(50), nullable=False, server_default="user_upload"),
        sa.Column("uploaded_by", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_microdata_datasets_country", "microdata_datasets", ["country_iso3"])
    op.create_index("ix_microdata_datasets_uploaded_by", "microdata_datasets", ["uploaded_by"])

    op.create_table(
        "microdata_variables",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("dataset_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("microdata_datasets.id"), nullable=False),
        sa.Column("variable_name", sa.String(255), nullable=False),
        sa.Column("variable_label", sa.Text(), nullable=True),
        sa.Column("value_labels", sa.JSON(), nullable=True),
        sa.Column("variable_index", sa.Integer(), nullable=True),
        sa.Column("inferred_dtype", sa.String(50), nullable=True),
        sa.Column("missing_count", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_microdata_variables_dataset", "microdata_variables", ["dataset_id"])

    op.create_table(
        "microdata_analysis_jobs",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("dataset_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("microdata_datasets.id"), nullable=False),
        sa.Column("job_type", sa.String(50), nullable=False),
        sa.Column("status", sa.String(50), nullable=False, server_default="pending"),
        sa.Column("parameters", sa.JSON(), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("requested_by", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
    )

    op.create_table(
        "microdata_analysis_results",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("job_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("microdata_analysis_jobs.id"), nullable=False),
        sa.Column("summary_stats", sa.JSON(), nullable=True),
        sa.Column("tables", sa.JSON(), nullable=True),
        sa.Column("charts", sa.JSON(), nullable=True),
        sa.Column("geojson", sa.JSON(), nullable=True),
        sa.Column("interpretation_text", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )


def downgrade() -> None:
    op.drop_table("microdata_analysis_results")
    op.drop_table("microdata_analysis_jobs")
    op.drop_index("ix_microdata_variables_dataset", table_name="microdata_variables")
    op.drop_table("microdata_variables")
    op.drop_index("ix_microdata_datasets_uploaded_by", table_name="microdata_datasets")
    op.drop_index("ix_microdata_datasets_country", table_name="microdata_datasets")
    op.drop_table("microdata_datasets")
    op.drop_table("microdata_projects")
