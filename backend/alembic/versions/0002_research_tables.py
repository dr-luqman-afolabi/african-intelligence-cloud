"""Research tables — Sprint 8 AI Research Assistant

Revision ID: 0002
Revises: 0001
Create Date: 2026-06-30

"""
from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
from alembic import op

revision: str = "0002"
down_revision: Union[str, None] = "0001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ------------------------------------------------------------------
    # research_sources
    # ------------------------------------------------------------------
    op.create_table(
        "research_sources",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("source_id", sa.String(100), nullable=False, unique=True, index=True),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("type", sa.String(100), nullable=False),
        sa.Column("api_url", sa.String(1000), nullable=True),
        sa.Column("license", sa.String(200), nullable=True),
        sa.Column("access_method", sa.String(100), nullable=False),
        sa.Column("citation_required", sa.Boolean, nullable=False, server_default="true"),
        sa.Column("rate_limit", sa.String(100), nullable=True),
        sa.Column("full_text_allowed", sa.Boolean, nullable=False, server_default="false"),
        sa.Column("metadata_only", sa.Boolean, nullable=False, server_default="true"),
        sa.Column("african_relevance_score", sa.Float, nullable=False, server_default="0.0"),
        sa.Column("description", sa.Text, nullable=True),
        sa.Column("is_active", sa.Boolean, server_default="true"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
    )

    # ------------------------------------------------------------------
    # research_papers
    # ------------------------------------------------------------------
    op.create_table(
        "research_papers",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("external_id", sa.String(500), nullable=True, index=True),
        sa.Column("doi", sa.String(500), nullable=True, unique=True, index=True),
        sa.Column("title", sa.Text, nullable=False),
        sa.Column("abstract", sa.Text, nullable=True),
        sa.Column("published_year", sa.Integer, nullable=True),
        sa.Column("journal", sa.String(500), nullable=True),
        sa.Column("volume", sa.String(50), nullable=True),
        sa.Column("issue", sa.String(50), nullable=True),
        sa.Column("pages", sa.String(100), nullable=True),
        sa.Column("open_access_url", sa.String(1000), nullable=True),
        sa.Column("is_open_access", sa.Boolean, server_default="false"),
        sa.Column("citation_count", sa.Integer, server_default="0"),
        sa.Column("language", sa.String(10), server_default="en"),
        sa.Column(
            "source_id", postgresql.UUID(as_uuid=True),
            sa.ForeignKey("research_sources.id", ondelete="SET NULL"), nullable=True
        ),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
    )

    # ------------------------------------------------------------------
    # paper_authors
    # ------------------------------------------------------------------
    op.create_table(
        "paper_authors",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "paper_id", postgresql.UUID(as_uuid=True),
            sa.ForeignKey("research_papers.id", ondelete="CASCADE"), nullable=False
        ),
        sa.Column("full_name", sa.String(500), nullable=False),
        sa.Column("affiliation", sa.String(500), nullable=True),
        sa.Column("orcid", sa.String(100), nullable=True),
        sa.Column("position", sa.Integer, nullable=True),
    )

    # ------------------------------------------------------------------
    # paper_topics
    # ------------------------------------------------------------------
    op.create_table(
        "paper_topics",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "paper_id", postgresql.UUID(as_uuid=True),
            sa.ForeignKey("research_papers.id", ondelete="CASCADE"), nullable=False
        ),
        sa.Column("topic", sa.String(255), nullable=False),
        sa.Column("score", sa.Float, nullable=True),
    )

    # ------------------------------------------------------------------
    # paper_citations
    # ------------------------------------------------------------------
    op.create_table(
        "paper_citations",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "paper_id", postgresql.UUID(as_uuid=True),
            sa.ForeignKey("research_papers.id", ondelete="CASCADE"), nullable=False
        ),
        sa.Column("cited_doi", sa.String(500), nullable=True),
        sa.Column("cited_title", sa.Text, nullable=True),
        sa.Column("cited_year", sa.Integer, nullable=True),
    )

    # ------------------------------------------------------------------
    # paper_datasets
    # ------------------------------------------------------------------
    op.create_table(
        "paper_datasets",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "paper_id", postgresql.UUID(as_uuid=True),
            sa.ForeignKey("research_papers.id", ondelete="CASCADE"), nullable=False
        ),
        sa.Column("dataset_name", sa.String(500), nullable=False),
        sa.Column("dataset_url", sa.String(1000), nullable=True),
        sa.Column("african_specific", sa.Boolean, server_default="false"),
    )

    # ------------------------------------------------------------------
    # paper_methods
    # ------------------------------------------------------------------
    op.create_table(
        "paper_methods",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "paper_id", postgresql.UUID(as_uuid=True),
            sa.ForeignKey("research_papers.id", ondelete="CASCADE"), nullable=False
        ),
        sa.Column("method_name", sa.String(255), nullable=False),
        sa.Column("method_type", sa.String(100), nullable=True),
    )

    # ------------------------------------------------------------------
    # paper_theories
    # ------------------------------------------------------------------
    op.create_table(
        "paper_theories",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "paper_id", postgresql.UUID(as_uuid=True),
            sa.ForeignKey("research_papers.id", ondelete="CASCADE"), nullable=False
        ),
        sa.Column("theory_name", sa.String(255), nullable=False),
        sa.Column("field", sa.String(100), nullable=True),
    )

    # ------------------------------------------------------------------
    # paper_policy_areas
    # ------------------------------------------------------------------
    op.create_table(
        "paper_policy_areas",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "paper_id", postgresql.UUID(as_uuid=True),
            sa.ForeignKey("research_papers.id", ondelete="CASCADE"), nullable=False
        ),
        sa.Column("area", sa.String(255), nullable=False),
        sa.Column("sdg_goal", sa.Integer, nullable=True),
    )


def downgrade() -> None:
    op.drop_table("paper_policy_areas")
    op.drop_table("paper_theories")
    op.drop_table("paper_methods")
    op.drop_table("paper_datasets")
    op.drop_table("paper_citations")
    op.drop_table("paper_topics")
    op.drop_table("paper_authors")
    op.drop_table("research_papers")
    op.drop_table("research_sources")
