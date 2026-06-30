"""Incremental synchronisation service.

Tracks per-source high-water marks (SyncWatermark) so each sync run fetches
only records that are new or updated since the previous run, avoiding full
re-ingestion of the entire catalogue on every schedule tick.
"""
from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy.orm import Session

from app.models.sync_watermark import SyncWatermark
from app.connectors.registry import CONNECTOR_REGISTRY
from app.services.connector_service import get_connector

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Watermark CRUD helpers
# ---------------------------------------------------------------------------

def get_watermark(db: Session, source_id: str) -> Optional[SyncWatermark]:
    return db.query(SyncWatermark).filter(SyncWatermark.source_id == source_id).first()


def upsert_watermark(
    db: Session,
    source_id: str,
    cursor: str,
    records_synced: int,
) -> SyncWatermark:
    wm = get_watermark(db, source_id)
    now = datetime.now(timezone.utc)
    if wm is None:
        wm = SyncWatermark(source_id=source_id)
        db.add(wm)
    wm.last_cursor = cursor
    wm.last_synced_at = now
    wm.records_synced = str(records_synced)
    db.commit()
    db.refresh(wm)
    return wm


def list_watermarks(db: Session) -> list[SyncWatermark]:
    return db.query(SyncWatermark).order_by(SyncWatermark.source_id).all()


# ---------------------------------------------------------------------------
# Incremental sync runner
# ---------------------------------------------------------------------------

def run_incremental_sync(db: Session, source_id: str) -> dict:
    """Run an incremental sync for one source, honouring the last watermark.

    The watermark cursor is passed as `since` kwarg to the connector's
    `sync()` (or `fetch()`) method. Connectors that don't support incremental
    fetch will ignore the kwarg and return all records — still correct,
    just not optimal for sources with huge catalogues.

    Returns a summary dict: {source_id, records_fetched, cursor, status}.
    """
    connector = get_connector(source_id)
    if connector is None:
        logger.warning("Incremental sync: no connector for %s", source_id)
        return {"source_id": source_id, "status": "no_connector", "records_fetched": 0}

    wm = get_watermark(db, source_id)
    since = wm.last_cursor if wm else None

    try:
        if hasattr(connector, "sync"):
            raw = connector.sync(since=since)
        else:
            raw = connector.fetch(since=since)

        normalised = connector.normalise(raw)
        count = len(normalised)

        # Cursor = ISO timestamp of this sync run
        new_cursor = datetime.now(timezone.utc).isoformat()
        upsert_watermark(db, source_id, new_cursor, count)

        logger.info("Incremental sync %s: %d records, cursor=%s", source_id, count, new_cursor)
        return {
            "source_id": source_id,
            "status": "ok",
            "records_fetched": count,
            "cursor": new_cursor,
        }
    except Exception as exc:
        logger.exception("Incremental sync failed for %s: %s", source_id, exc)
        return {"source_id": source_id, "status": "error", "message": str(exc), "records_fetched": 0}


def run_all_incremental(db: Session) -> list[dict]:
    """Run incremental sync for every registered connector."""
    results = []
    for source_id in CONNECTOR_REGISTRY:
        results.append(run_incremental_sync(db, source_id))
    return results
