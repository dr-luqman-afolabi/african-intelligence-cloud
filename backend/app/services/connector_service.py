from __future__ import annotations

import logging
from datetime import datetime, timezone
from uuid import uuid4

from sqlalchemy.orm import Session

from app.connectors.base import BaseConnector, ConnectorError, HealthStatus
from app.connectors.registry import REGISTRY
from app.models.data_source import DataSource
from app.models.sync_job import SyncJob
from app.models.data_lineage import DataLineage

logger = logging.getLogger(__name__)

# Module-level connector map: source_id → BaseConnector instance
_CONNECTORS: dict[str, BaseConnector] = {}


def register_connector(connector: BaseConnector) -> None:
    """Register a connector instance. Called by each connector module at import time."""
    _CONNECTORS[connector.source_id] = connector
    logger.info("Registered connector: %s", connector.source_id)


def get_connector(source_id: str) -> BaseConnector:
    if source_id not in _CONNECTORS:
        raise KeyError(f"No connector registered for source_id='{source_id}'")
    return _CONNECTORS[source_id]


def list_connectors() -> list[dict]:
    """Return registry metadata merged with live/planned connector status."""
    result = []
    for meta in REGISTRY.values():
        sid = meta["source_id"]
        result.append({
            **meta,
            "connector_registered": sid in _CONNECTORS,
        })
    return result


def seed_data_sources(db: Session) -> None:
    """Upsert all registry entries into the data_sources table."""
    for meta in REGISTRY.values():
        existing = db.query(DataSource).filter(DataSource.source_id == meta["source_id"]).first()
        if existing:
            for k, v in meta.items():
                if k != "source_id":
                    setattr(existing, k, v)
        else:
            db.add(DataSource(**meta))
    db.commit()


def run_sync(db: Session, source_id: str, **kwargs) -> SyncJob:
    """
    Execute a full sync for one source:
      1. Create a SyncJob row (status=running)
      2. Call connector.sync() → normalised records
      3. Write to postgres via ingestion_service
      4. Compute quality score
      5. Record lineage
      6. Update SyncJob (status=success|failed)
    Returns the completed SyncJob.
    """
    job = SyncJob(
        id=uuid4(),
        source_id=source_id,
        status="running",
        started_at=datetime.now(timezone.utc),
    )
    db.add(job)
    db.commit()

    try:
        connector = get_connector(source_id)
        records = connector.sync(**kwargs)

        from app.services.ingestion_service import ingest_records, ingest_to_bigquery
        written = ingest_records(db, source_id, records)

        # Mirror to BigQuery when configured (non-blocking: errors are logged, not raised)
        bq_errors = ingest_to_bigquery(source_id, records)
        bq_dest = "bigquery" if not bq_errors else "bigquery_error"

        from app.services.quality_service import compute_quality
        compute_quality(db, job.id, source_id, records)

        # Lineage: postgres leg
        db.add(DataLineage(
            sync_job_id=job.id,
            source_id=source_id,
            destination="postgres",
            destination_table="macro_data",
            row_count=written,
            pipeline_version="1.0",
        ))

        # Lineage: BigQuery leg (only when configured)
        if records:
            from app.config import get_settings
            if get_settings().bigquery_dataset:
                db.add(DataLineage(
                    sync_job_id=job.id,
                    source_id=source_id,
                    destination=bq_dest,
                    destination_table="connector_data",
                    row_count=len(records),
                    pipeline_version="1.0",
                ))

        # Update catalog entry after successful sync
        try:
            from app.services.catalog_service import upsert_catalog_entry
            upsert_catalog_entry(db, source_id, records)
        except Exception:
            logger.debug("Catalog update skipped for %s", source_id)

        # Push metadata to DataHub (non-blocking; skipped when GMS URL not configured)
        try:
            from app.services.datahub_service import push_dataset_metadata
            dh_meta = REGISTRY.get(source_id, {})
            push_dataset_metadata(source_id, records, source_name=dh_meta.get("source_name", ""))
        except Exception:
            logger.debug("DataHub push skipped for %s", source_id)

        job.status = "success"
        job.records_fetched = len(records)
        job.records_written = written
        job.finished_at = datetime.now(timezone.utc)
        db.commit()
        logger.info("Sync complete: source=%s written=%d bq_errors=%d", source_id, written, len(bq_errors))

    except ConnectorError as exc:
        job.status = "failed"
        job.error_message = str(exc)
        job.finished_at = datetime.now(timezone.utc)
        db.commit()
        logger.error("Sync failed: source=%s error=%s", source_id, exc)

    except Exception as exc:
        job.status = "failed"
        job.error_message = f"Unexpected error: {exc}"
        job.finished_at = datetime.now(timezone.utc)
        db.commit()
        logger.exception("Sync unexpected error: source=%s", source_id)

    return job


def get_health(source_id: str) -> HealthStatus:
    connector = get_connector(source_id)
    return connector.health_check()


def get_lineage(db: Session, source_id: str, limit: int = 20) -> list[DataLineage]:
    return (
        db.query(DataLineage)
        .filter(DataLineage.source_id == source_id)
        .order_by(DataLineage.created_at.desc())
        .limit(limit)
        .all()
    )
