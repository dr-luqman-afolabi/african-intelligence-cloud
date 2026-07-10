"""Public API for HarvestStat-Africa harmonized subnational crop statistics.

Open-access crop area/production/yield across African countries, admin regions,
crops, seasons and years — served as metadata + multi-series time series. No
auth: openly-licensed data.
"""
from __future__ import annotations

from fastapi import APIRouter, Query

from app.services import harveststat_service as hs

router = APIRouter(prefix="/harveststat", tags=["HarvestStat Crop Statistics"])


@router.get("/meta", summary="Catalog: countries, crops, seasons, metrics, year range")
def harveststat_meta():
    return hs.get_meta()


@router.get("/series", summary="Multi-series crop time series (yield/production/area)")
def harveststat_series(
    countries: list[str] | None = Query(default=None),
    crops: list[str] | None = Query(default=None),
    metric: str = "yield",
    admin_1: str | None = None,
    season: str | None = None,
):
    return hs.get_series(countries, crops, metric, admin_1, season)
