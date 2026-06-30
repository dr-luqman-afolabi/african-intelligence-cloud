"""APScheduler-based automatic sync scheduler for AIC connectors.

Uses BackgroundScheduler (thread-based) so it works with standard WSGI/ASGI
without requiring a separate process. Each enabled SyncSchedule row becomes
a cron job. The scheduler is started in the FastAPI lifespan and stopped on
shutdown.
"""
from __future__ import annotations

import logging
from datetime import datetime, timezone
from uuid import uuid4

from sqlalchemy.orm import Session

from app.database import SessionLocal
from app.models.sync_schedule import SyncSchedule

logger = logging.getLogger(__name__)

_scheduler = None


# ---------------------------------------------------------------------------
# Internal job function (runs in scheduler thread)
# ---------------------------------------------------------------------------

def _run_sync_job(source_id: str) -> None:
    db: Session = SessionLocal()
    try:
        from app.services.connector_service import run_sync
        logger.info("Scheduled sync triggered: source=%s", source_id)
        job = run_sync(db, source_id)
        logger.info("Scheduled sync complete: source=%s status=%s", source_id, job.status)

        schedule = db.query(SyncSchedule).filter(SyncSchedule.source_id == source_id).first()
        if schedule:
            schedule.last_triggered_at = datetime.now(timezone.utc)
            db.commit()
    except Exception:
        logger.exception("Scheduled sync error: source=%s", source_id)
    finally:
        db.close()


# ---------------------------------------------------------------------------
# Scheduler lifecycle
# ---------------------------------------------------------------------------

def start_scheduler(db: Session) -> None:
    global _scheduler
    try:
        from apscheduler.schedulers.background import BackgroundScheduler
        from apscheduler.triggers.cron import CronTrigger
    except ImportError:
        logger.warning("APScheduler not installed — sync scheduler disabled")
        return

    _scheduler = BackgroundScheduler(timezone="UTC")
    schedules = db.query(SyncSchedule).filter(SyncSchedule.enabled == True).all()  # noqa: E712
    for sched in schedules:
        _add_job(sched)

    _scheduler.start()
    logger.info("Sync scheduler started with %d jobs", len(schedules))


def stop_scheduler() -> None:
    global _scheduler
    if _scheduler and _scheduler.running:
        _scheduler.shutdown(wait=False)
        logger.info("Sync scheduler stopped")
    _scheduler = None


def _add_job(sched: SyncSchedule) -> None:
    if _scheduler is None:
        return
    from apscheduler.triggers.cron import CronTrigger
    job_id = f"sync_{sched.source_id}"
    _scheduler.add_job(
        _run_sync_job,
        trigger=CronTrigger(
            minute=sched.cron_minute,
            hour=sched.cron_hour,
            day=sched.cron_day,
            month=sched.cron_month,
            day_of_week=sched.cron_day_of_week,
        ),
        id=job_id,
        args=[sched.source_id],
        replace_existing=True,
        misfire_grace_time=300,
    )
    logger.info("Scheduled job added: source=%s cron=%s", sched.source_id, sched.cron_expression)


def _remove_job(source_id: str) -> None:
    if _scheduler is None:
        return
    job_id = f"sync_{source_id}"
    if _scheduler.get_job(job_id):
        _scheduler.remove_job(job_id)


# ---------------------------------------------------------------------------
# CRUD helpers
# ---------------------------------------------------------------------------

def upsert_schedule(db: Session, source_id: str, cron_minute: str = "0",
                    cron_hour: str = "2", cron_day: str = "*",
                    cron_month: str = "*", cron_day_of_week: str = "*",
                    enabled: bool = True) -> SyncSchedule:
    sched = db.query(SyncSchedule).filter(SyncSchedule.source_id == source_id).first()
    if sched is None:
        sched = SyncSchedule(id=uuid4(), source_id=source_id)
        db.add(sched)

    sched.cron_minute = cron_minute
    sched.cron_hour = cron_hour
    sched.cron_day = cron_day
    sched.cron_month = cron_month
    sched.cron_day_of_week = cron_day_of_week
    sched.enabled = enabled
    db.commit()
    db.refresh(sched)

    if enabled:
        _add_job(sched)
    else:
        _remove_job(source_id)

    return sched


def delete_schedule(db: Session, source_id: str) -> bool:
    sched = db.query(SyncSchedule).filter(SyncSchedule.source_id == source_id).first()
    if sched is None:
        return False
    _remove_job(source_id)
    db.delete(sched)
    db.commit()
    return True


def list_schedules(db: Session) -> list[SyncSchedule]:
    return db.query(SyncSchedule).all()


def get_schedule(db: Session, source_id: str) -> SyncSchedule | None:
    return db.query(SyncSchedule).filter(SyncSchedule.source_id == source_id).first()


def trigger_now(db: Session, source_id: str) -> None:
    """Fire a sync job immediately (outside its regular schedule)."""
    from apscheduler.triggers.date import DateTrigger
    if _scheduler is None:
        _run_sync_job(source_id)
        return
    job_id = f"sync_immediate_{source_id}_{uuid4().hex[:6]}"
    _scheduler.add_job(
        _run_sync_job,
        trigger=DateTrigger(run_date=datetime.now(timezone.utc)),
        id=job_id,
        args=[source_id],
    )
