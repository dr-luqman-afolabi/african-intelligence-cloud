from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import Column, String, Integer, DateTime, Text, JSON
from sqlalchemy.dialects.postgresql import UUID

from app.database import Base


class DatasetDOI(Base):
    """DOI index for research datasets harvested from external registries.

    Each row represents one citable digital object, keyed by its DOI.
    Supports citation-level lineage tracking and deduplication across sources.
    """

    __tablename__ = "dataset_dois"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    doi = Column(String(512), nullable=False, unique=True, index=True)
    source_id = Column(String, nullable=False, index=True)   # datacite, zenodo, …
    title = Column(Text, nullable=True)
    publisher = Column(String(512), nullable=True)
    publication_year = Column(Integer, nullable=True)
    country_iso3 = Column(String(3), nullable=True, index=True)
    resource_type = Column(String(128), nullable=True)
    license_url = Column(Text, nullable=True)
    subjects = Column(JSON, nullable=True)          # list[str] of subject tags
    creators = Column(JSON, nullable=True)          # list[{name, affiliation}]
    raw_metadata = Column(JSON, nullable=True)      # full API response attributes
    indexed_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )
