"""Source health monitoring router.

Exposes /api/v1/health/sources with per-connector health status, suitable
for an ops dashboard that shows which data sources are reachable and how fast.
"""
from __future__ import annotations

import asyncio
import logging
import time
from concurrent.futures import ThreadPoolExecutor, wait
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.services.connector_service import get_connector
from app.services.incremental_sync_service import list_watermarks
from app.connectors.registry import CONNECTOR_REGISTRY

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/health/sources", tags=["Health"])

# Hard cap (seconds) on how long the aggregated dashboard endpoint will wait
# for slow/unreachable external connectors before returning a partial result.
_AGGREGATE_DEADLINE_SECONDS = 8.0

# Shared, bounded, module-level pool for connector health checks. Reusing a
# single pool (instead of creating a fresh ThreadPoolExecutor per request)
# prevents unbounded thread growth when requests abandon slow/hanging
# connector checks at the deadline: worker threads are recycled once their
# current (possibly abandoned) task finishes, rather than piling up one
# fresh batch of threads per request indefinitely.
_HEALTH_CHECK_POOL = ThreadPoolExecutor(max_workers=20, thread_name_prefix="health-check")


# ---------------------------------------------------------------------------
# Single-source health
# ---------------------------------------------------------------------------

@router.get("/{source_id}")
def source_health(source_id: str, db: Session = Depends(get_db)):
    """Return health status for one registered connector."""
    try:
        connector = get_connector(source_id)
    except KeyError:
        raise HTTPException(status_code=404, detail=f"No connector registered for source_id='{source_id}'")

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
    filter to reachable sources only. Individual connector checks run
    concurrently on a shared, bounded thread pool and are limited to
    _AGGREGATE_DEADLINE_SECONDS in total so that a single slow or
    unreachable external source can never stall the whole dashboard
    response — any check still running when the deadline hits is reported
    as timed out instead of blocking the request.
    """
    all_ids = sorted(CONNECTOR_REGISTRY.keys())
    page_ids = all_ids[skip : skip + limit]

    # Pull watermark data once for metadata augmentation
    watermarks = {wm.source_id: wm for wm in list_watermarks(db)}

    def _check_one(source_id: str) -> dict:
        try:
            connector = get_connector(source_id)
        except KeyError:
            return {"source_id": source_id, "healthy": None, "message": "no connector"}
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
        wm = watermarks.get(source_id)
        entry["last_synced_at"] = wm.last_synced_at.isoformat() if (wm and wm.last_synced_at) else None
        entry["records_synced"] = wm.records_synced if wm else None
        reg = CONNECTOR_REGISTRY.get(source_id, {})
        entry["source_name"] = reg.get("source_name", source_id)
        entry["license_category"] = reg.get("license_category")
        entry["update_frequency"] = reg.get("update_frequency")
        return entry

    futures = {_HEALTH_CHECK_POOL.submit(_check_one, sid): sid for sid in page_ids}
    done, not_done = wait(futures.keys(), timeout=_AGGREGATE_DEADLINE_SECONDS)

    checked = []
    for future in done:
        source_id = futures[future]
        try:
            checked.append(future.result())
        except Exception as exc:
            checked.append({"source_id": source_id, "healthy": False, "message": str(exc)})
    for future in not_done:
        source_id = futures[future]
        checked.append({
            "source_id": source_id,
            "healthy": False,
            "message": "health check timed out",
        })
        # Don't cancel: the shared pool's worker will simply pick up the next
        # queued task once this one finishes, so we deliberately avoid
        # blocking here rather than tearing down any executor.

    checked.sort(key=lambda e: e.get("source_id") or "")
    results = [e for e in checked if not (healthy_only and not e.get("healthy"))]

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
