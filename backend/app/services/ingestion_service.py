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

    for rec in records:
        iso3 = rec.get("country_iso3", "").upper()
        code = rec.get("indicator_code", "")
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

        existing = (
            db.query(MacroData)
            .filter(
                MacroData.country_id == country.id,
                MacroData.indicator_id == indicator.id,
                MacroData.year == year,
            )
            .first()
        )
        if existing:
            existing.value = value
            existing.data_source = rec.get("data_source", source_id)
        else:
            db.add(MacroData(
                country_id=country.id,
                indicator_id=indicator.id,
                year=year,
                value=value,
                data_source=rec.get("data_source", source_id),
            ))
        written += 1

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
