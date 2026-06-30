from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import Column, String, DateTime, Text
from sqlalchemy.dialects.postgresql import UUID

from app.database import Base


class SyncWatermark(Base):
    """Tracks the high-water mark for incremental synchronisation per source.

    Each row holds the last successfully synced cursor for one data source.
    The cursor format is source-specific (ISO timestamp, page token, offset, etc.).
    """

    __tablename__ = "sync_watermarks"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    source_id = Column(String, nullable=False, unique=True, index=True)
    # Last cursor successfully committed — type depends on source convention
    last_cursor = Column(Text, nullable=True)
    last_synced_at = Column(DateTime(timezone=True), nullable=True)
    records_synced = Column(String, nullable=True)  # cumulative count as string to avoid int overflow
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )
