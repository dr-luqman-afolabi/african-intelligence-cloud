from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import Column, String, Integer, Boolean, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.database import Base


class SurveyRound(Base):
    __tablename__ = "survey_rounds"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    survey_id = Column(String, ForeignKey("surveys.survey_id", ondelete="CASCADE"), nullable=False, index=True)
    round_label = Column(String)          # e.g. "Round 7", "Wave 3", "2018-19"
    year_start = Column(Integer)
    year_end = Column(Integer)
    sample_size = Column(Integer)
    fieldwork_start = Column(String)
    fieldwork_end = Column(String)
    catalog_id = Column(String)           # external catalog identifier
    data_available = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    survey = relationship("Survey", back_populates="rounds")
