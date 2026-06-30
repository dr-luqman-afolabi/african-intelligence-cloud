"""Initial schema — all AIC tables through Sprint 5

Revision ID: 0001
Revises:
Create Date: 2026-06-30

"""
from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
from alembic import op

revision: str = "0001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ------------------------------------------------------------------
    # organizations
    # ------------------------------------------------------------------
    op.create_table(
        "organizations",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("name", sa.String(255), nullable=False, unique=True),
        sa.Column("description", sa.Text),
        sa.Column("website", sa.String(512)),
        sa.Column("created_at", sa.DateTime(timezone=True)),
        sa.Column("updated_at", sa.DateTime(timezone=True)),
    )

    # ------------------------------------------------------------------
    # users
    # ------------------------------------------------------------------
    op.create_table(
        "users",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("email", sa.String(320), nullable=False, unique=True, index=True),
        sa.Column("hashed_password", sa.String(1024), nullable=False),
        sa.Column("full_name", sa.String(255)),
        sa.Column("role", sa.String(50), nullable=False, server_default="viewer"),
        sa.Column("is_active", sa.Boolean, nullable=False, server_default="true"),
        sa.Column("organization_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("organizations.id", ondelete="SET NULL"), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True)),
        sa.Column("updated_at", sa.DateTime(timezone=True)),
    )
    op.create_index("ix_users_email", "users", ["email"])

    # ------------------------------------------------------------------
    # countries
    # ------------------------------------------------------------------
    op.create_table(
        "countries",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("iso3", sa.String(3), nullable=False, unique=True, index=True),
        sa.Column("iso2", sa.String(2)),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("region", sa.String(100)),
        sa.Column("sub_region", sa.String(100)),
        sa.Column("income_group", sa.String(100)),
        sa.Column("capital", sa.String(255)),
        sa.Column("population", sa.BigInteger),
        sa.Column("area_sq_km", sa.Float),
        sa.Column("created_at", sa.DateTime(timezone=True)),
        sa.Column("updated_at", sa.DateTime(timezone=True)),
    )

    # ------------------------------------------------------------------
    # indicators
    # ------------------------------------------------------------------
    op.create_table(
        "indicators",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("code", sa.String(255), nullable=False, unique=True, index=True),
        sa.Column("name", sa.String(512), nullable=False),
        sa.Column("description", sa.Text),
        sa.Column("category", sa.String(100)),
        sa.Column("unit", sa.String(100)),
        sa.Column("source", sa.String(255)),
        sa.Column("created_at", sa.DateTime(timezone=True)),
        sa.Column("updated_at", sa.DateTime(timezone=True)),
    )

    # ------------------------------------------------------------------
    # data_sources
    # ------------------------------------------------------------------
    op.create_table(
        "data_sources",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("source_id", sa.String(100), nullable=False, unique=True, index=True),
        sa.Column("source_name", sa.String(255), nullable=False),
        sa.Column("description", sa.Text),
        sa.Column("base_url", sa.String(512)),
        sa.Column("license_category", sa.String(10)),
        sa.Column("connector_status", sa.String(50)),
        sa.Column("update_frequency", sa.String(50)),
        sa.Column("is_active", sa.Boolean, nullable=False, server_default="true"),
        sa.Column("created_at", sa.DateTime(timezone=True)),
        sa.Column("updated_at", sa.DateTime(timezone=True)),
    )

    # ------------------------------------------------------------------
    # macro_data
    # ------------------------------------------------------------------
    op.create_table(
        "macro_data",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("country_iso3", sa.String(3), nullable=False, index=True),
        sa.Column("indicator_code", sa.String(255), nullable=False, index=True),
        sa.Column("year", sa.Integer, nullable=False),
        sa.Column("value", sa.Float),
        sa.Column("unit", sa.String(100)),
        sa.Column("data_source", sa.String(255)),
        sa.Column("source_id", sa.String(100), index=True),
        sa.Column("metadata", postgresql.JSON),
        sa.Column("created_at", sa.DateTime(timezone=True)),
        sa.Column("updated_at", sa.DateTime(timezone=True)),
    )
    op.create_index("ix_macro_data_country_indicator_year",
                    "macro_data", ["country_iso3", "indicator_code", "year"])

    # ------------------------------------------------------------------
    # audit_logs
    # ------------------------------------------------------------------
    op.create_table(
        "audit_logs",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("action", sa.String(100), nullable=False),
        sa.Column("resource_type", sa.String(100)),
        sa.Column("resource_id", sa.String(255)),
        sa.Column("details", postgresql.JSON),
        sa.Column("ip_address", sa.String(45)),
        sa.Column("created_at", sa.DateTime(timezone=True)),
    )

    # ------------------------------------------------------------------
    # uploaded_datasets (and related)
    # ------------------------------------------------------------------
    op.create_table(
        "uploaded_datasets",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("name", sa.String(512), nullable=False),
        sa.Column("description", sa.Text),
        sa.Column("file_path", sa.String(1024)),
        sa.Column("file_size_bytes", sa.BigInteger),
        sa.Column("mime_type", sa.String(255)),
        sa.Column("status", sa.String(50), nullable=False, server_default="pending"),
        sa.Column("privacy", sa.String(50), nullable=False, server_default="private"),
        sa.Column("row_count", sa.BigInteger),
        sa.Column("column_count", sa.Integer),
        sa.Column("owner_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("organization_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("organizations.id", ondelete="SET NULL"), nullable=True),
        sa.Column("gcs_uri", sa.String(1024)),
        sa.Column("bq_table_id", sa.String(512)),
        sa.Column("created_at", sa.DateTime(timezone=True)),
        sa.Column("updated_at", sa.DateTime(timezone=True)),
    )

    op.create_table(
        "dataset_columns",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("dataset_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("uploaded_datasets.id", ondelete="CASCADE"), nullable=False),
        sa.Column("name", sa.String(512), nullable=False),
        sa.Column("dtype", sa.String(100)),
        sa.Column("null_count", sa.BigInteger),
        sa.Column("unique_count", sa.BigInteger),
        sa.Column("sample_values", postgresql.JSON),
    )

    op.create_table(
        "dataset_profiles",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("dataset_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("uploaded_datasets.id", ondelete="CASCADE"), nullable=False, unique=True),
        sa.Column("profile_json", postgresql.JSON),
        sa.Column("created_at", sa.DateTime(timezone=True)),
    )

    op.create_table(
        "analysis_jobs",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("dataset_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("uploaded_datasets.id", ondelete="CASCADE"), nullable=False),
        sa.Column("job_type", sa.String(100), nullable=False),
        sa.Column("status", sa.String(50), nullable=False, server_default="pending"),
        sa.Column("result", postgresql.JSON),
        sa.Column("error_message", sa.Text),
        sa.Column("created_at", sa.DateTime(timezone=True)),
        sa.Column("completed_at", sa.DateTime(timezone=True)),
    )

    # ------------------------------------------------------------------
    # sync_jobs
    # ------------------------------------------------------------------
    op.create_table(
        "sync_jobs",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("source_id", sa.String(100), nullable=False, index=True),
        sa.Column("status", sa.String(50), nullable=False, server_default="pending"),
        sa.Column("records_fetched", sa.Integer, server_default="0"),
        sa.Column("records_inserted", sa.Integer, server_default="0"),
        sa.Column("error_message", sa.Text),
        sa.Column("started_at", sa.DateTime(timezone=True)),
        sa.Column("completed_at", sa.DateTime(timezone=True)),
        sa.Column("created_at", sa.DateTime(timezone=True)),
    )

    # ------------------------------------------------------------------
    # data_lineage
    # ------------------------------------------------------------------
    op.create_table(
        "data_lineage",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("source_table", sa.String(255), nullable=False),
        sa.Column("source_id_ref", sa.String(255)),
        sa.Column("target_table", sa.String(255), nullable=False),
        sa.Column("target_id_ref", sa.String(255)),
        sa.Column("transformation", sa.Text),
        sa.Column("created_at", sa.DateTime(timezone=True)),
    )

    # ------------------------------------------------------------------
    # quality_scores
    # ------------------------------------------------------------------
    op.create_table(
        "quality_scores",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("source_id", sa.String(100), nullable=False, index=True),
        sa.Column("indicator_code", sa.String(255), index=True),
        sa.Column("score", sa.Float),
        sa.Column("completeness", sa.Float),
        sa.Column("timeliness", sa.Float),
        sa.Column("accuracy", sa.Float),
        sa.Column("details", postgresql.JSON),
        sa.Column("evaluated_at", sa.DateTime(timezone=True)),
    )

    # ------------------------------------------------------------------
    # catalog_entries
    # ------------------------------------------------------------------
    op.create_table(
        "catalog_entries",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("source_id", sa.String(100), nullable=False, index=True),
        sa.Column("indicator_code", sa.String(512), nullable=False, index=True),
        sa.Column("country_iso3", sa.String(3), index=True),
        sa.Column("year", sa.Integer),
        sa.Column("value", sa.Float),
        sa.Column("unit", sa.String(100)),
        sa.Column("data_source", sa.String(255)),
        sa.Column("metadata", postgresql.JSON),
        sa.Column("created_at", sa.DateTime(timezone=True)),
        sa.Column("updated_at", sa.DateTime(timezone=True)),
    )
    op.create_index("ix_catalog_entries_source_country_year",
                    "catalog_entries", ["source_id", "country_iso3", "year"])

    # ------------------------------------------------------------------
    # surveys
    # ------------------------------------------------------------------
    op.create_table(
        "surveys",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("source_id", sa.String(100), nullable=False, index=True),
        sa.Column("survey_code", sa.String(255), nullable=False, unique=True, index=True),
        sa.Column("title", sa.String(512), nullable=False),
        sa.Column("description", sa.Text),
        sa.Column("country_iso3", sa.String(3), index=True),
        sa.Column("survey_type", sa.String(100)),
        sa.Column("organization", sa.String(255)),
        sa.Column("created_at", sa.DateTime(timezone=True)),
        sa.Column("updated_at", sa.DateTime(timezone=True)),
    )

    # ------------------------------------------------------------------
    # survey_rounds
    # ------------------------------------------------------------------
    op.create_table(
        "survey_rounds",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("survey_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("surveys.id", ondelete="CASCADE"), nullable=False),
        sa.Column("round_number", sa.Integer),
        sa.Column("year", sa.Integer, index=True),
        sa.Column("year_end", sa.Integer),
        sa.Column("sample_size", sa.Integer),
        sa.Column("microdata_url", sa.String(1024)),
        sa.Column("report_url", sa.String(1024)),
        sa.Column("access_type", sa.String(50)),
        sa.Column("created_at", sa.DateTime(timezone=True)),
    )

    # ------------------------------------------------------------------
    # sync_schedules
    # ------------------------------------------------------------------
    op.create_table(
        "sync_schedules",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("source_id", sa.String(100), nullable=False, unique=True, index=True),
        sa.Column("cron_minute", sa.String(20), server_default="0"),
        sa.Column("cron_hour", sa.String(20), server_default="2"),
        sa.Column("cron_day", sa.String(20), server_default="*"),
        sa.Column("cron_month", sa.String(20), server_default="*"),
        sa.Column("cron_day_of_week", sa.String(20), server_default="*"),
        sa.Column("enabled", sa.Boolean, nullable=False, server_default="true"),
        sa.Column("last_triggered_at", sa.DateTime(timezone=True)),
        sa.Column("next_run_at", sa.DateTime(timezone=True)),
        sa.Column("created_at", sa.DateTime(timezone=True)),
        sa.Column("updated_at", sa.DateTime(timezone=True)),
    )

    # ------------------------------------------------------------------
    # sync_watermarks  (Sprint 5 — incremental sync)
    # ------------------------------------------------------------------
    op.create_table(
        "sync_watermarks",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("source_id", sa.String(100), nullable=False, unique=True, index=True),
        sa.Column("last_cursor", sa.Text, nullable=True),
        sa.Column("last_synced_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("records_synced", sa.String(30), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True)),
        sa.Column("updated_at", sa.DateTime(timezone=True)),
    )

    # ------------------------------------------------------------------
    # dataset_dois  (Sprint 5 — DOI index)
    # ------------------------------------------------------------------
    op.create_table(
        "dataset_dois",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("doi", sa.String(512), nullable=False, unique=True, index=True),
        sa.Column("source_id", sa.String(100), nullable=False, index=True),
        sa.Column("title", sa.Text, nullable=True),
        sa.Column("publisher", sa.String(512), nullable=True),
        sa.Column("publication_year", sa.Integer, nullable=True),
        sa.Column("country_iso3", sa.String(3), nullable=True, index=True),
        sa.Column("resource_type", sa.String(128), nullable=True),
        sa.Column("license_url", sa.Text, nullable=True),
        sa.Column("subjects", postgresql.JSON, nullable=True),
        sa.Column("creators", postgresql.JSON, nullable=True),
        sa.Column("raw_metadata", postgresql.JSON, nullable=True),
        sa.Column("indexed_at", sa.DateTime(timezone=True)),
        sa.Column("updated_at", sa.DateTime(timezone=True)),
    )


def downgrade() -> None:
    op.drop_table("dataset_dois")
    op.drop_table("sync_watermarks")
    op.drop_table("sync_schedules")
    op.drop_table("survey_rounds")
    op.drop_table("surveys")
    op.drop_index("ix_catalog_entries_source_country_year", table_name="catalog_entries")
    op.drop_table("catalog_entries")
    op.drop_table("quality_scores")
    op.drop_table("data_lineage")
    op.drop_table("sync_jobs")
    op.drop_table("analysis_jobs")
    op.drop_table("dataset_profiles")
    op.drop_table("dataset_columns")
    op.drop_table("uploaded_datasets")
    op.drop_table("audit_logs")
    op.drop_index("ix_macro_data_country_indicator_year", table_name="macro_data")
    op.drop_table("macro_data")
    op.drop_table("data_sources")
    op.drop_table("indicators")
    op.drop_table("countries")
    op.drop_index("ix_users_email", table_name="users")
    op.drop_table("users")
    op.drop_table("organizations")
