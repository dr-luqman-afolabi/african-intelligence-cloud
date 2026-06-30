from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import Column, String, Integer, Float, DateTime, JSON
from sqlalchemy.dialects.postgresql import UUID

from app.database import Base


class CatalogEntry(Base):
    __tablename__ = "catalog_entries"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    source_id = Column(String, nullable=False, index=True, unique=True)
    source_name = Column(String)
    total_records = Column(Integer, default=0)
    countries_covered = Column(JSON, default=list)
    indicators_covered = Column(JSON, default=list)
    year_min = Column(Integer)
    year_max = Column(Integer)
    last_synced_at = Column(DateTime(timezone=True))
    avg_completeness = Column(Float)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc),
                        onupdate=lambda: datetime.now(timezone.utc))
