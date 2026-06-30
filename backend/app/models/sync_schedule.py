from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import Column, String, Integer, Boolean, DateTime
from sqlalchemy.dialects.postgresql import UUID

from app.database import Base


class SyncSchedule(Base):
    __tablename__ = "sync_schedules"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    source_id = Column(String, nullable=False, unique=True, index=True)
    # APScheduler cron fields (all default to * = every)
    cron_minute = Column(String, default="0")
    cron_hour = Column(String, default="2")
    cron_day = Column(String, default="*")
    cron_month = Column(String, default="*")
    cron_day_of_week = Column(String, default="*")
    enabled = Column(Boolean, default=True, nullable=False)
    last_triggered_at = Column(DateTime(timezone=True))
    next_run_at = Column(DateTime(timezone=True))
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc),
                        onupdate=lambda: datetime.now(timezone.utc))

    @property
    def cron_expression(self) -> str:
        return (f"{self.cron_minute} {self.cron_hour} "
                f"{self.cron_day} {self.cron_month} {self.cron_day_of_week}")
