from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import Column, String, Boolean, DateTime, JSON
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.database import Base


class Survey(Base):
    __tablename__ = "surveys"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    survey_id = Column(String, unique=True, nullable=False, index=True)
    title = Column(String, nullable=False)
    series = Column(String)               # e.g. "DHS", "LSMS", "AFROBAROMETER"
    source_id = Column(String, index=True) # links to connectors registry
    country_iso3 = Column(String, index=True)
    primary_topic = Column(String)        # e.g. "health", "poverty", "governance"
    requires_approval = Column(Boolean, default=True)
    redistribution_allowed = Column(Boolean, default=False)
    microdata_available = Column(Boolean, default=False)
    access_url = Column(String)
    documentation_url = Column(String)
    tags = Column(JSON, default=list)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc),
                        onupdate=lambda: datetime.now(timezone.utc))

    rounds = relationship("SurveyRound", back_populates="survey", cascade="all, delete-orphan")
