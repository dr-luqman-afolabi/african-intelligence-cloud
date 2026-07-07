import logging
from uuid import UUID

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.database import get_db
from app.services.auth_service import get_current_user
from app.services.connector_service import (
    get_connector,
    get_health,
    get_lineage,
    list_connectors,
    run_sync,
)
from app.models.sync_job import SyncJob
from app.models.quality_score import QualityScore

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/connectors", tags=["connectors"])
security = HTTPBearer()


def _get_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db),
):
    return get_current_user(db, credentials.credentials)


@router.get("")
def list_all_connectors(current_user=Depends(_get_user)):
    """List all registered data source connectors with their metadata."""
    return list_connectors()


@router.get("/{source_id}/health")
def connector_health(source_id: str, current_user=Depends(_get_user)):
    """Probe the upstream source and return health status."""
    try:
        status = get_health(source_id)
        return {
            "source_id": status.source_id,
            "healthy": status.healthy,
            "latency_ms": status.latency_ms,
            "message": status.message,
            "checked_at": status.checked_at.isoformat(),
        }
    except KeyError:
        raise HTTPException(status_code=404, detail=f"No connector for source_id='{source_id}'")


@router.post("/{source_id}/sync")
def trigger_sync(
    source_id: str,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user=Depends(_get_user),
):
    """Trigger a background sync for the given source."""
    try:
        get_connector(source_id)
    except KeyError:
        raise HTTPException(status_code=404, detail=f"No connector for source_id='{source_id}'")

    def _run():
        from app.database import SessionLocal
        _db = SessionLocal()
        try:
            run_sync(_db, source_id)
        finally:
            _db.close()

    background_tasks.add_task(_run)
    return {"message": f"Sync started for source_id='{source_id}'", "source_id": source_id}


@router.get("/{source_id}/sync/history")
def sync_history(
    source_id: str,
    limit: int = 20,
    db: Session = Depends(get_db),
    current_user=Depends(_get_user),
):
    """Return the last N sync jobs for a source."""
    jobs = (
        db.query(SyncJob)
        .filter(SyncJob.source_id == source_id)
        .order_by(SyncJob.created_at.desc())
        .limit(min(limit, 100))
        .all()
    )
    return [
        {
            "id": str(j.id),
            "source_id": j.source_id,
            "status": j.status,
            "records_fetched": j.records_fetched,
            "records_written": j.records_written,
            "error_message": j.error_message,
            "started_at": j.started_at.isoformat() if j.started_at else None,
            "finished_at": j.finished_at.isoformat() if j.finished_at else None,
        }
        for j in jobs
    ]


@router.get("/{source_id}/lineage")
def connector_lineage(
    source_id: str,
    limit: int = 20,
    db: Session = Depends(get_db),
    current_user=Depends(_get_user),
):
    """Return data lineage records for a source."""
    rows = get_lineage(db, source_id, limit=min(limit, 100))
    return [
        {
            "id": str(r.id),
            "sync_job_id": str(r.sync_job_id),
            "source_id": r.source_id,
            "destination": r.destination,
            "destination_table": r.destination_table,
            "row_count": r.row_count,
            "pipeline_version": r.pipeline_version,
            "created_at": r.created_at.isoformat() if r.created_at else None,
        }
        for r in rows
    ]


@router.get("/{source_id}/quality")
def connector_quality(
    source_id: str,
    limit: int = 10,
    db: Session = Depends(get_db),
    current_user=Depends(_get_user),
):
    """Return quality score history for a source."""
    scores = (
        db.query(QualityScore)
        .filter(QualityScore.source_id == source_id)
        .order_by(QualityScore.computed_at.desc())
        .limit(min(limit, 50))
        .all()
    )
    return [
        {
            "id": str(s.id),
            "sync_job_id": str(s.sync_job_id),
            "overall_score": s.overall_score,
            "completeness_score": s.completeness_score,
            "timeliness_score": s.timeliness_score,
            "coverage_score": s.coverage_score,
            "consistency_score": s.consistency_score,
            "total_records": s.total_records,
            "null_count": s.null_count,
            "outlier_count": s.outlier_count,
            "computed_at": s.computed_at.isoformat() if s.computed_at else None,
        }
        for s in scores
    ]
