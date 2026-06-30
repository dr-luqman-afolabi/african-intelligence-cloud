from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.database import get_db
from app.services.scheduler_service import (
    upsert_schedule,
    delete_schedule,
    list_schedules,
    get_schedule,
    trigger_now,
)

router = APIRouter(prefix="/schedules", tags=["Sync Scheduler"])


class ScheduleRequest(BaseModel):
    cron_minute: str = "0"
    cron_hour: str = "2"
    cron_day: str = "*"
    cron_month: str = "*"
    cron_day_of_week: str = "*"
    enabled: bool = True


@router.get("", summary="List all sync schedules")
def list_all(db: Session = Depends(get_db)):
    return [_sched_dict(s) for s in list_schedules(db)]


@router.get("/{source_id}", summary="Get schedule for a source")
def get_one(source_id: str, db: Session = Depends(get_db)):
    s = get_schedule(db, source_id)
    if s is None:
        raise HTTPException(status_code=404, detail=f"No schedule for source_id={source_id!r}")
    return _sched_dict(s)


@router.put("/{source_id}", summary="Create or update a sync schedule")
def upsert(source_id: str, body: ScheduleRequest, db: Session = Depends(get_db)):
    s = upsert_schedule(
        db, source_id,
        cron_minute=body.cron_minute,
        cron_hour=body.cron_hour,
        cron_day=body.cron_day,
        cron_month=body.cron_month,
        cron_day_of_week=body.cron_day_of_week,
        enabled=body.enabled,
    )
    return _sched_dict(s)


@router.delete("/{source_id}", summary="Delete a sync schedule")
def delete(source_id: str, db: Session = Depends(get_db)):
    removed = delete_schedule(db, source_id)
    if not removed:
        raise HTTPException(status_code=404, detail=f"No schedule for source_id={source_id!r}")
    return {"status": "deleted", "source_id": source_id}


@router.post("/{source_id}/trigger", summary="Trigger an immediate sync outside schedule")
def trigger(source_id: str, db: Session = Depends(get_db)):
    trigger_now(db, source_id)
    return {"status": "triggered", "source_id": source_id}


def _sched_dict(s) -> dict:
    return {
        "source_id": s.source_id,
        "cron_expression": s.cron_expression,
        "cron_minute": s.cron_minute,
        "cron_hour": s.cron_hour,
        "cron_day": s.cron_day,
        "cron_month": s.cron_month,
        "cron_day_of_week": s.cron_day_of_week,
        "enabled": s.enabled,
        "last_triggered_at": s.last_triggered_at.isoformat() if s.last_triggered_at else None,
        "next_run_at": s.next_run_at.isoformat() if s.next_run_at else None,
        "updated_at": s.updated_at.isoformat() if s.updated_at else None,
    }
