from __future__ import annotations

import logging
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.models.catalog_entry import CatalogEntry
from app.connectors.registry import REGISTRY

logger = logging.getLogger(__name__)


def upsert_catalog_entry(db: Session, source_id: str, records: list[dict]) -> CatalogEntry:
    """Update or create a catalog entry from a completed sync's normalised records."""
    entry = db.query(CatalogEntry).filter(CatalogEntry.source_id == source_id).first()
    if entry is None:
        meta = REGISTRY.get(source_id, {})
        entry = CatalogEntry(
            source_id=source_id,
            source_name=meta.get("source_name", source_id),
        )
        db.add(entry)

    if records:
        countries = sorted({r["country_iso3"] for r in records if r.get("country_iso3")})
        indicators = sorted({r["indicator_code"] for r in records if r.get("indicator_code")})
        years = [r["year"] for r in records if r.get("year") is not None]
        values = [r["value"] for r in records if r.get("value") is not None]
        non_null = sum(1 for v in values if v is not None)

        entry.total_records = len(records)
        entry.countries_covered = countries
        entry.indicators_covered = indicators
        entry.year_min = min(years) if years else None
        entry.year_max = max(years) if years else None
        entry.avg_completeness = round(non_null / len(records), 4) if records else None

    entry.last_synced_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(entry)
    logger.info("Catalog entry updated: source=%s records=%d", source_id, len(records))
    return entry


def get_catalog_entry(db: Session, source_id: str) -> CatalogEntry | None:
    return db.query(CatalogEntry).filter(CatalogEntry.source_id == source_id).first()


def list_catalog_entries(db: Session, skip: int = 0, limit: int = 100) -> list[CatalogEntry]:
    return db.query(CatalogEntry).offset(skip).limit(limit).all()
