import uuid
from sqlalchemy import Column, String, Boolean, Float, DateTime, Uuid, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base


class ResearchSource(Base):
    __tablename__ = "research_sources"

    id = Column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    source_id = Column(String(100), nullable=False, unique=True, index=True)
    name = Column(String(255), nullable=False)
    type = Column(String(100), nullable=False)  # academic_database | preprint | institutional_repo | grey_literature
    api_url = Column(String(1000), nullable=True)
    license = Column(String(200), nullable=True)
    access_method = Column(String(100), nullable=False)  # open_api | oauth | registration | scrape
    citation_required = Column(Boolean, nullable=False, default=True)
    rate_limit = Column(String(100), nullable=True)  # e.g. "100/day"
    full_text_allowed = Column(Boolean, nullable=False, default=False)
    metadata_only = Column(Boolean, nullable=False, default=True)
    african_relevance_score = Column(Float, nullable=False, default=0.0)  # 0.0–1.0
    description = Column(Text, nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    papers = relationship("ResearchPaper", back_populates="source")
