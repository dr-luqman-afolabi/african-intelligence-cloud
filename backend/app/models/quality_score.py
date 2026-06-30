import uuid
from sqlalchemy import Column, String, Float, Integer, DateTime, Text, Uuid, ForeignKey, Index
from sqlalchemy.sql import func
from app.database import Base


class QualityScore(Base):
    """Quality assessment for a sync job's output."""

    __tablename__ = "quality_scores"

    id = Column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    sync_job_id = Column(Uuid(as_uuid=True), ForeignKey("sync_jobs.id"), nullable=False, index=True)
    source_id = Column(String(100), nullable=False, index=True)

    # Overall score 0–100
    overall_score = Column(Float, nullable=False, default=0.0)

    # Component scores 0–100
    completeness_score = Column(Float, nullable=True)   # non-null values / total
    consistency_score = Column(Float, nullable=True)    # values within expected range
    timeliness_score = Column(Float, nullable=True)     # most-recent year vs current year
    coverage_score = Column(Float, nullable=True)       # countries covered / target countries

    total_records = Column(Integer, nullable=True)
    null_count = Column(Integer, nullable=True)
    outlier_count = Column(Integer, nullable=True)
    notes = Column(Text, nullable=True)

    computed_at = Column(DateTime(timezone=True), server_default=func.now())

    __table_args__ = (
        Index("ix_quality_scores_source", "source_id", "computed_at"),
    )
