from __future__ import annotations

import logging
from uuid import uuid4

from sqlalchemy.orm import Session

from app.models.macro_data import MacroData
from app.models.country import Country
from app.models.indicator import Indicator

logger = logging.getLogger(__name__)


def ingest_records(db: Session, source_id: str, records: list[dict]) -> int:
    """
    Upsert normalised connector records into macro_data.

    Expected canonical record fields:
      country_iso3, indicator_code, year, value, unit, data_source, source_id
    Returns count of rows written/updated.
    """
    if not records:
        return 0

    country_cache: dict[str, Country | None] = {}
    indicator_cache: dict[str, Indicator | None] = {}
    written = 0

    # Pre-load the existing rows this payload could collide with, in one query.
    # This used to be a SELECT per record: with ~40k records and the database in
    # us-central1 while the refresh job runs in africa-south1, those round trips
    # alone took hours, so the job hit its task timeout before ever reaching the
    # commit below — and every fetched record was discarded.
    codes = {
        (r.get("indicator_code") or "")
        for r in records
        if isinstance(r, dict) and r.get("indicator_code")
    }
    existing_ids: dict[tuple[str, str, int], int] = {}
    if codes:
        for row in (
            db.query(
                MacroData.id,
                MacroData.country_iso3,
                MacroData.indicator_code,
                MacroData.year,
            )
            .filter(MacroData.indicator_code.in_(codes))
            .all()
        ):
            existing_ids[(row.country_iso3, row.indicator_code, row.year)] = row.id

    inserts: list[dict] = []
    updates: list[dict] = []
    seen_new: set[tuple[str, str, int]] = set()

    for rec in records:
        # Catalogue-style sources (DOI indexes, survey/microdata listings) emit
        # records that aren't country-indicator series at all — missing or null
        # country_iso3, or not even a mapping. They have nothing to contribute
        # to macro_data, so skip them rather than raising: a `.get(k, "")` on a
        # key that exists with a None value returns None, and None.upper()
        # would abort the whole source's ingestion.
        if not isinstance(rec, dict):
            continue
        iso3 = (rec.get("country_iso3") or "").upper()
        code = rec.get("indicator_code") or ""
        year = rec.get("year")
        value = rec.get("value")

        if not iso3 or not code or year is None or value is None:
            continue

        if iso3 not in country_cache:
            country_cache[iso3] = db.query(Country).filter(Country.iso3 == iso3).first()
        country = country_cache[iso3]
        if not country:
            continue

        if code not in indicator_cache:
            indicator_cache[code] = db.query(Indicator).filter(Indicator.code == code).first()
        indicator = indicator_cache[code]
        if not indicator:
            logger.debug("Skipping unknown indicator: %s", code)
            continue

        key = (iso3, code, year)
        row_id = existing_ids.get(key)
        if row_id is not None:
            updates.append({
                "id": row_id,
                "value": value,
                "data_source": rec.get("data_source", source_id),
            })
        elif key not in seen_new:
            # Guard against duplicates inside one payload, which would violate
            # the uniqueness the per-row SELECT used to enforce implicitly.
            seen_new.add(key)
            inserts.append({
                "country_iso3": iso3,
                "indicator_code": code,
                "year": year,
                "value": value,
                "data_source": rec.get("data_source", source_id),
            })
        written += 1

    if inserts:
        db.bulk_insert_mappings(MacroData, inserts)
    if updates:
        db.bulk_update_mappings(MacroData, updates)
    db.commit()
    return written


def ingest_to_bigquery(source_id: str, records: list[dict]) -> list[dict]:
    """
    Stream normalised records to BigQuery `aic_analytics.connector_data`.
    Returns BigQuery insert errors (empty list = success).
    Gracefully skips if BigQuery is not configured.
    """
    from app.config import get_settings
    settings = get_settings()
    if not settings.bigquery_dataset:
        logger.debug("BigQuery not configured; skipping BQ ingest for %s", source_id)
        return []

    try:
        from app.services.bigquery_service import insert_rows
        rows = [
            {**rec, "source_id": source_id}
            for rec in records
        ]
        return insert_rows(settings.bigquery_dataset, "connector_data", rows)
    except Exception as exc:
        logger.error("BigQuery ingest failed for %s: %s", source_id, exc)
        return [{"error": str(exc)}]
