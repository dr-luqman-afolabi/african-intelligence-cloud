"""Automatic metadata extraction service.

On every ingest of normalised records this service extracts schema-level
statistics (field presence, value ranges, completeness %) and stores them
as a lightweight profile alongside the DatasetDOI or CatalogEntry record.

The extraction is intentionally lightweight — it runs in-process during sync
so it must complete in milliseconds per batch, not seconds.
"""
from __future__ import annotations

import logging
from typing import Any

from sqlalchemy.orm import Session

from app.models.dataset_doi import DatasetDOI

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Schema-level profiling helpers
# ---------------------------------------------------------------------------

def _field_stats(records: list[dict], field: str) -> dict:
    """Return presence rate and (for numeric fields) min/max/mean."""
    values = [r.get(field) for r in records if r.get(field) is not None]
    total = len(records)
    present = len(values)
    stats: dict[str, Any] = {
        "presence_pct": round(present / total * 100, 1) if total else 0,
        "count": present,
    }
    numeric = [v for v in values if isinstance(v, (int, float))]
    if numeric:
        stats["min"] = min(numeric)
        stats["max"] = max(numeric)
        stats["mean"] = round(sum(numeric) / len(numeric), 4)
    return stats


def extract_batch_profile(records: list[dict]) -> dict:
    """Compute a lightweight profile for a batch of normalised records.

    Returns a dict suitable for storing in JSON metadata columns.
    """
    if not records:
        return {"record_count": 0}

    canonical_fields = [
        "country_iso3", "indicator_code", "year", "value", "unit",
        "data_source", "source_id",
    ]
    profile: dict[str, Any] = {"record_count": len(records)}
    for f in canonical_fields:
        profile[f] = _field_stats(records, f)

    countries = {r.get("country_iso3") for r in records if r.get("country_iso3")}
    years = [r.get("year") for r in records if isinstance(r.get("year"), int)]
    profile["country_count"] = len(countries)
    profile["year_range"] = [min(years), max(years)] if years else []

    return profile


# ---------------------------------------------------------------------------
# DOI-specific extraction
# ---------------------------------------------------------------------------

def extract_and_index_doi(db: Session, normalised: dict) -> DatasetDOI:
    """Upsert one normalised DataCite record into the dataset_dois table.

    Creates a new row or updates the existing one if the DOI already exists.
    """
    doi = normalised.get("metadata", {}).get("doi", "")
    if not doi:
        raise ValueError("normalised record is missing doi in metadata")

    row = db.query(DatasetDOI).filter(DatasetDOI.doi == doi).first()
    meta = normalised.get("metadata", {})

    if row is None:
        row = DatasetDOI(doi=doi)
        db.add(row)

    row.source_id = normalised.get("source_id", "datacite")
    row.title = meta.get("title")
    row.publisher = meta.get("publisher")
    row.publication_year = int(normalised["year"]) if normalised.get("year") else None
    row.country_iso3 = normalised.get("country_iso3")
    row.resource_type = meta.get("resource_type")
    row.license_url = meta.get("license_url")
    row.raw_metadata = meta

    db.commit()
    db.refresh(row)
    return row


def index_doi_batch(db: Session, records: list[dict], source_id: str = "datacite") -> int:
    """Bulk-index a list of normalised DataCite records. Returns count indexed."""
    indexed = 0
    for r in records:
        if r.get("source_id") != source_id:
            continue
        try:
            extract_and_index_doi(db, r)
            indexed += 1
        except Exception as exc:
            logger.debug("DOI index failed for record %s: %s", r.get("indicator_code"), exc)
    return indexed
