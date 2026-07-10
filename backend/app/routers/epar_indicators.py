"""Public API for EPAR agricultural-development indicator estimates.

Open-access LSMS-ISA-derived indicators (5 countries, 27 waves, 150 indicators)
served as metadata + multi-series time series for charting. No auth: this is
openly-disseminated aggregate data.
"""
from __future__ import annotations

from fastapi import APIRouter, Query

from app.services import epar_indicators_service as epar

router = APIRouter(prefix="/epar", tags=["EPAR Ag Indicators"])


@router.get("/meta", summary="Indicator catalog: countries, categories, indicators, disaggregations")
def epar_meta():
    return epar.get_meta()


@router.get("/series", summary="Multi-series time series for the selected countries/indicators")
def epar_series(
    countries: list[str] | None = Query(default=None),
    indicators: list[str] | None = Query(default=None),
    gender: str | None = None,
    farmsize: str | None = None,
    commodity: str | None = None,
    rural: str | None = None,
):
    return epar.get_series(countries, indicators, gender, farmsize, commodity, rural)
