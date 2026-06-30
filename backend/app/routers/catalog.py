from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
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
