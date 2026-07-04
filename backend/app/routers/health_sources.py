"""Source health monitoring router.

Exposes /api/v1/health/sources with per-connector health status, suitable
for an ops dashboard that shows which data sources are reachable and how fast.
"""
from __future__ import annotations

import asyncio
import logging
import time
from typing import Annotated

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.services.connector_service import get_connector
from app.services.incremental_sync_service import list_watermarks
from app.connectors.registry import CONNECTOR_REGISTRY

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/health/sources", tags=["Health"])


# ---------------------------------------------------------------------------
# Single-source health
# ---------------------------------------------------------------------------

@router.get("/{source_id}")
def source_health(source_id: str, db: Session = Depends(get_db)):
    """Return health status for one registered connector."""
    connector = get_connector(source_id)
    if connector is None:
        return {"source_id": source_id, "error": "connector not found"}

    try:
        status = connector.health_check()
        return {
            "source_id": status.source_id,
            "healthy": status.healthy,
            "latency_ms": status.latency_ms,
            "message": status.message,
            "checked_at": status.checked_at.isoformat(),
        }
    except Exception as exc:
        logger.exception("Health check failed for %s", source_id)
        return {"source_id": source_id, "healthy": False, "message": str(exc)}


# ---------------------------------------------------------------------------
# Aggregated dashboard
# ---------------------------------------------------------------------------

@router.get("")
def all_sources_health(
    db: Session = Depends(get_db),
    limit: Annotated[int, Query(ge=1, le=200)] = 50,
    skip: Annotated[int, Query(ge=0)] = 0,
    healthy_only: bool = False,
):
    """Return aggregated health status for all registered connectors.

    Results are paginated (default 50 per page). Pass healthy_only=true to
    filter to reachable sources only.
    """
    all_ids = sorted(CONNECTOR_REGISTRY.keys())
    page_ids = all_ids[skip : skip + limit]

    # Pull watermark data once for metadata augmentation
    watermarks = {wm.source_id: wm for wm in list_watermarks(db)}

    results = []
    for source_id in page_ids:
        try:
            connector = get_connector(source_id)
        except KeyError:
            results.append({"source_id": source_id, "healthy": None, "message": "no connector"})
            continue

        try:
            status = connector.health_check()
            entry = {
                "source_id": status.source_id,
                "healthy": status.healthy,
                "latency_ms": status.latency_ms,
                "message": status.message,
                "checked_at": status.checked_at.isoformat() if status.checked_at else None,
            }
        except Exception as exc:
            entry = {"source_id": source_id, "healthy": False, "message": str(exc)}

        # Augment with last-sync info
        wm = watermarks.get(source_id)
        entry["last_synced_at"] = wm.last_synced_at.isoformat() if (wm and wm.last_synced_at) else None
        entry["records_synced"] = wm.records_synced if wm else None

        # Augment with registry metadata
        reg = CONNECTOR_REGISTRY.get(source_id, {})
        entry["source_name"] = reg.get("source_name", source_id)
        entry["license_category"] = reg.get("license_category")
        entry["update_frequency"] = reg.get("update_frequency")

        if healthy_only and not entry.get("healthy"):
            continue
        results.append(entry)

    healthy_count = sum(1 for r in results if r.get("healthy"))
    return {
        "total_sources": len(all_ids),
        "page": {"skip": skip, "limit": limit, "returned": len(results)},
        "summary": {
            "healthy": healthy_count,
            "unhealthy": len(results) - healthy_count,
        },
        "sources": results,
    }
