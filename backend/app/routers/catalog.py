from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session

from app.database import get_db
from app.services.catalog_service import (
    list_catalog_entries,
    get_catalog_entry,
)

router = APIRouter(prefix="/catalog", tags=["Catalog"])


@router.get("", summary="List all catalog entries")
def list_entries(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    entries = list_catalog_entries(db, skip=skip, limit=limit)
    return [_to_dict(e) for e in entries]


@router.get("/{source_id}", summary="Get catalog entry for a source")
def get_entry(source_id: str, db: Session = Depends(get_db)):
    entry = get_catalog_entry(db, source_id)
    if entry is None:
        raise HTTPException(status_code=404, detail=f"No catalog entry for source_id={source_id!r}")
    return _to_dict(entry)


@router.post("/{source_id}/push-to-datahub", summary="Push source metadata to DataHub")
def push_to_datahub(
    source_id: str,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
):
    entry = get_catalog_entry(db, source_id)
    if entry is None:
        raise HTTPException(status_code=404, detail=f"No catalog entry for source_id={source_id!r}")

    def _push():
        from app.services.datahub_service import push_dataset_metadata
        result = push_dataset_metadata(
            source_id=source_id,
            records=[],  # catalog entry already aggregated — pass empty; stats come from entry
            source_name=entry.source_name or source_id,
        )
        return result

    background_tasks.add_task(_push)
    return {"status": "queued", "source_id": source_id,
            "message": "DataHub push queued as background task"}


def _to_dict(e) -> dict:
    return {
        "source_id": e.source_id,
        "source_name": e.source_name,
        "total_records": e.total_records,
        "countries_covered": e.countries_covered or [],
        "indicators_covered": e.indicators_covered or [],
        "year_min": e.year_min,
        "year_max": e.year_max,
        "last_synced_at": e.last_synced_at.isoformat() if e.last_synced_at else None,
        "avg_completeness": e.avg_completeness,
        "updated_at": e.updated_at.isoformat() if e.updated_at else None,
    }
