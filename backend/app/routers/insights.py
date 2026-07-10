"""Public AI Insights endpoint — grounded interpretation of a plotted series."""
from __future__ import annotations

from typing import Any

from fastapi import APIRouter
from pydantic import BaseModel, Field

from app.services import insights_service

router = APIRouter(prefix="/insights", tags=["AI Insights"])


class SeriesPoint(BaseModel):
    year: int
    value: float | None = None


class InsightSeries(BaseModel):
    label: str | None = None
    country: str | None = None
    crop: str | None = None
    units: str | None = None
    points: list[SeriesPoint] = Field(default_factory=list)


class InsightRequest(BaseModel):
    action: str = "interpret"
    title: str | None = None
    metric: str | None = None
    series: list[InsightSeries] = Field(default_factory=list)


@router.post("/series")
def series_insight(req: InsightRequest) -> dict[str, Any]:
    payload = {
        "action": req.action,
        "title": req.title,
        "metric": req.metric,
        "series": [
            {"label": s.label, "country": s.country, "crop": s.crop, "units": s.units,
             "points": [{"year": p.year, "value": p.value} for p in s.points]}
            for s in req.series
        ],
    }
    return insights_service.generate(payload)
