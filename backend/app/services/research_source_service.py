"""Service layer for research source seeding and retrieval."""
from __future__ import annotations

import uuid
from sqlalchemy.orm import Session

from app.models.research_source import ResearchSource
from app.data.research_sources_registry import RESEARCH_SOURCES


def seed_research_sources(db: Session) -> None:
    """Upsert all registry sources into the database."""
    for record in RESEARCH_SOURCES:
        existing = db.query(ResearchSource).filter(
            ResearchSource.source_id == record["source_id"]
        ).first()
        if not existing:
            db.add(ResearchSource(id=uuid.uuid4(), **record))
    db.commit()


def list_sources(db: Session, active_only: bool = True) -> list[ResearchSource]:
    q = db.query(ResearchSource)
    if active_only:
        q = q.filter(ResearchSource.is_active.is_(True))
    return q.order_by(ResearchSource.african_relevance_score.desc()).all()


def get_source(db: Session, source_id: str) -> ResearchSource | None:
    return db.query(ResearchSource).filter(ResearchSource.source_id == source_id).first()
