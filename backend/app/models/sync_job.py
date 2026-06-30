import uuid
from sqlalchemy import Column, String, Integer, DateTime, Text, Uuid, ForeignKey, Index
from sqlalchemy.sql import func
from app.database import Base


class SyncJob(Base):
    __tablename__ = "sync_jobs"

    id = Column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    source_id = Column(String(100), ForeignKey("data_sources.source_id"), nullable=False, index=True)
    # pending | running | success | failed | partial
    status = Column(String(20), nullable=False, default="pending")
    records_fetched = Column(Integer, nullable=True)
    records_written = Column(Integer, nullable=True)
    error_message = Column(Text, nullable=True)
    started_at = Column(DateTime(timezone=True), nullable=True)
    finished_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    __table_args__ = (
        Index("ix_sync_jobs_source_created", "source_id", "created_at"),
    )
