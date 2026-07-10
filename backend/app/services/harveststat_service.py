"""HarvestStat-Africa harmonized subnational crop statistics.

Serves the open-access harmonized crop dataset published by HarvestStat:
  https://github.com/HarvestStat/HarvestStat-Africa

The file is tidy long-format — one row per
(country, admin unit, crop, season, harvest year) with area, production and
yield. This module fetches it once from GitHub, slims and caches it in-process,
and answers metadata + multi-series time-series queries so several
countries/crops can be drawn as separate lines on one chart. Nothing is stored
on disk; every failure path leaves the cache empty and the API returns an
empty/loading result rather than erroring.
"""
from __future__ import annotations

import io
import logging
import threading
from typing import Any

import pandas as pd
import requests

logger = logging.getLogger(__name__)

_URL = (
    "https://raw.githubusercontent.com/HarvestStat/HarvestStat-Africa/main/"
    "public/hvstat_africa_data_v1.2.csv"
)
_KEEP = [
    "country", "country_code", "admin_1", "product", "season_name",
    "harvest_year", "area", "production", "yield",
]
_METRICS = {"yield": "Yield (t/ha)", "production": "Production (t)", "area": "Area (ha)"}
_DF: pd.DataFrame | None = None
_LOCK = threading.Lock()
_LOAD_FAILED = False


def _load() -> pd.DataFrame:
    global _DF, _LOAD_FAILED
    if _DF is not None:
        return _DF
    with _LOCK:
        if _DF is not None:
            return _DF
        try:
            resp = requests.get(_URL, timeout=90)
            resp.raise_for_status()
            frames = []
            reader = pd.read_csv(
                io.BytesIO(resp.content), usecols=_KEEP, chunksize=100000,
                dtype={"country": "string", "admin_1": "string", "product": "string",
                       "season_name": "string"},
            )
            for chunk in reader:
                frames.append(chunk)
            df = pd.concat(frames, ignore_index=True) if frames else pd.DataFrame(columns=_KEEP)
            for c in ("harvest_year", "area", "production", "yield"):
                df[c] = pd.to_numeric(df[c], errors="coerce")
            df = df.dropna(subset=["harvest_year"])
            df["harvest_year"] = df["harvest_year"].astype(int)
            _DF = df
            logger.info("HarvestStat loaded: %d rows", len(df))
        except Exception as exc:
            logger.warning("Could not load HarvestStat data (%s)", exc)
            _LOAD_FAILED = True
            _DF = pd.DataFrame(columns=_KEEP)
    return _DF


def _uniq(series: pd.Series) -> list[str]:
    return sorted(str(v) for v in series.dropna().unique() if str(v) not in ("", "none", "nan"))


def get_meta() -> dict[str, Any]:
    df = _load()
    if df.empty:
        return {"loaded": not _LOAD_FAILED, "countries": [], "crops": [],
                "crops_by_country": {}, "seasons": [], "metrics": _METRICS,
                "year_min": None, "year_max": None}
    crops_by_country: dict[str, list[str]] = {}
    for country in _uniq(df["country"]):
        crops_by_country[country] = _uniq(df[df["country"] == country]["product"])
    return {
        "loaded": True,
        "countries": _uniq(df["country"]),
        "crops": _uniq(df["product"]),
        "crops_by_country": crops_by_country,
        "seasons": _uniq(df["season_name"]),
        "metrics": _METRICS,
        "year_min": int(df["harvest_year"].min()),
        "year_max": int(df["harvest_year"].max()),
        "row_count": int(len(df)),
    }


def get_series(
    countries: list[str] | None,
    crops: list[str] | None,
    metric: str = "yield",
    admin_1: str | None = None,
    season: str | None = None,
) -> dict[str, Any]:
    """One time series per (country x crop) selection for a multi-line chart.

    Area/production are summed across admin units; yield is recomputed as
    production/area so national aggregates stay correct.
    """
    df = _load()
    if df.empty:
        return {"series": [], "metric": metric, "loaded": not _LOAD_FAILED}
    if metric not in _METRICS:
        metric = "yield"

    sub = df
    if countries:
        sub = sub[sub["country"].isin(countries)]
    if crops:
        sub = sub[sub["product"].isin(crops)]
    if admin_1:
        sub = sub[sub["admin_1"] == admin_1]
    if season:
        sub = sub[sub["season_name"] == season]
    if sub.empty:
        return {"series": [], "metric": metric, "loaded": True}

    grouped = (
        sub.groupby(["country", "product", "harvest_year"], observed=True)[["area", "production"]]
        .sum(min_count=1)
        .reset_index()
    )
    grouped["yield"] = grouped.apply(
        lambda r: (r["production"] / r["area"]) if r["area"] and r["area"] > 0 else None, axis=1
    )

    series = []
    for (country, crop), grp in grouped.groupby(["country", "product"], observed=True):
        grp = grp.sort_values("harvest_year")
        pts = []
        for _, r in grp.iterrows():
            val = r[metric]
            if pd.isna(val):
                continue
            pts.append({"x": str(int(r["harvest_year"])), "year": int(r["harvest_year"]),
                        "value": round(float(val), 3)})
        if pts:
            series.append({
                "label": f"{country} — {crop}",
                "country": country, "crop": crop,
                "units": _METRICS[metric], "points": pts,
            })
    return {"series": series, "metric": metric, "units": _METRICS[metric], "loaded": True}
