import uuid
from sqlalchemy import Column, String, DateTime, Text, Uuid, ForeignKey, Index, Integer
from sqlalchemy.sql import func
from app.database import Base


class DataLineage(Base):
    """One row per sync_job, recording what was ingested and where it landed."""

    __tablename__ = "data_lineage"

    id = Column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    sync_job_id = Column(Uuid(as_uuid=True), ForeignKey("sync_jobs.id"), nullable=False, index=True)
    source_id = Column(String(100), nullable=False, index=True)
    # postgres | bigquery | gcs
    destination = Column(String(50), nullable=False, default="postgres")
    destination_table = Column(String(255), nullable=True)
    row_count = Column(Integer, nullable=True)
    schema_snapshot = Column(Text, nullable=True)  # JSON string of column names/types
    pipeline_version = Column(String(50), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    __table_args__ = (
        Index("ix_data_lineage_source", "source_id", "created_at"),
    )
