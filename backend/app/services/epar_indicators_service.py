"""EPAR agricultural-development indicator estimates.

Serves the open-access cross-country indicator estimates that EPAR (Evans
School Policy Analysis & Research) constructs from the LSMS-ISA surveys and
disseminates for reuse:
  https://github.com/EvansSchoolPolicyAnalysisAndResearch/LSMS-Data-Dissemination

The estimates are a tidy long-format panel — one row per
(country, survey wave, indicator, disaggregation) with mean/sd/percentiles —
covering 5 countries, 27 survey waves and 150 indicators. This module fetches
that file once from GitHub, slims and caches it in-process, and answers
metadata + multi-series time-series queries so the frontend can draw several
indicators/countries as separate lines on one chart.

Nothing is stored on disk; every failure path leaves the cache empty and the
API returns an empty or loading result rather than erroring.
"""
from __future__ import annotations

import io
import logging
import re
import threading
from typing import Any

import pandas as pd
import requests

logger = logging.getLogger(__name__)

_URL = (
    "https://raw.githubusercontent.com/EvansSchoolPolicyAnalysisAndResearch/"
    "LSMS-Data-Dissemination/main/EPAR_UW_335_AgDev_Indicator_Estimates.dta"
)
_KEEP = [
    "Geography", "Instrument", "Year", "indicatorcategory", "indicatorname",
    "units", "commoditydisaggregation", "genderdisaggregation",
    "hhfarmsizedisaggregation", "ruraltotalpopulation", "mean", "sd", "p50", "N",
]
_DF: pd.DataFrame | None = None
_LOCK = threading.Lock()
_LOAD_FAILED = False


def _wave_num(instrument: str) -> int:
    m = re.search(r"wave\s*(\d+)", str(instrument).lower())
    return int(m.group(1)) if m else 0


def _year_start(year: str) -> int:
    m = re.search(r"(\d{4})", str(year))
    return int(m.group(1)) if m else 0


def _load() -> pd.DataFrame:
    """Fetch + slim + cache the estimates. Returns an empty frame on failure."""
    global _DF, _LOAD_FAILED
    if _DF is not None:
        return _DF
    with _LOCK:
        if _DF is not None:
            return _DF
        try:
            resp = requests.get(_URL, timeout=60)
            resp.raise_for_status()
            frames = []
            reader = pd.read_stata(
                io.BytesIO(resp.content), columns=_KEEP,
                convert_categoricals=False, chunksize=20000,
            )
            for chunk in reader:
                frames.append(chunk)
            df = pd.concat(frames, ignore_index=True) if frames else pd.DataFrame(columns=_KEEP)
            for c in ("mean", "sd", "p50", "N"):
                df[c] = pd.to_numeric(df[c], errors="coerce")
            df["_wave"] = df["Instrument"].map(_wave_num)
            df["_year"] = df["Year"].map(_year_start)
            _DF = df
            logger.info("EPAR indicators loaded: %d rows", len(df))
        except Exception as exc:
            logger.warning("Could not load EPAR indicators (%s)", exc)
            _LOAD_FAILED = True
            _DF = pd.DataFrame(columns=_KEEP + ["_wave", "_year"])
    return _DF


def _uniq(series: pd.Series) -> list[str]:
    vals = [str(v) for v in series.dropna().unique() if str(v) not in ("", "N/A", "nan")]
    return sorted(vals)


def get_meta() -> dict[str, Any]:
    df = _load()
    if df.empty:
        return {"loaded": not _LOAD_FAILED, "countries": [], "categories": [],
                "indicators_by_category": {}, "gender": [], "farmsize": [],
                "commodity": [], "rural": []}
    indicators_by_cat: dict[str, list[str]] = {}
    for cat in _uniq(df["indicatorcategory"]):
        names = _uniq(df[df["indicatorcategory"] == cat]["indicatorname"])
        indicators_by_cat[cat] = names
    return {
        "loaded": True,
        "countries": _uniq(df["Geography"]),
        "categories": _uniq(df["indicatorcategory"]),
        "indicators_by_category": indicators_by_cat,
        "gender": _uniq(df["genderdisaggregation"]),
        "farmsize": _uniq(df["hhfarmsizedisaggregation"]),
        "commodity": _uniq(df["commoditydisaggregation"]),
        "rural": _uniq(df["ruraltotalpopulation"]),
        "row_count": int(len(df)),
    }


def get_series(
    countries: list[str] | None,
    indicators: list[str] | None,
    gender: str | None = None,
    farmsize: str | None = None,
    commodity: str | None = None,
    rural: str | None = None,
) -> dict[str, Any]:
    """Return one time-series per (country x indicator) selection for a multi-line chart."""
    df = _load()
    if df.empty:
        return {"series": [], "waves": [], "loaded": not _LOAD_FAILED}

    countries = countries or []
    indicators = indicators or []
    sub = df
    if countries:
        sub = sub[sub["Geography"].isin(countries)]
    if indicators:
        sub = sub[sub["indicatorname"].isin(indicators)]
    if gender:
        sub = sub[sub["genderdisaggregation"] == gender]
    if farmsize:
        sub = sub[sub["hhfarmsizedisaggregation"] == farmsize]
    if commodity:
        sub = sub[sub["commoditydisaggregation"] == commodity]
    if rural:
        sub = sub[sub["ruraltotalpopulation"] == rural]

    # Shared, ordered wave axis (label = "Country Wave N (year)").
    axis = (
        sub[["Geography", "Instrument", "_wave", "_year", "Year"]]
        .drop_duplicates()
        .sort_values(["_year", "_wave"])
    )
    series = []
    for (country, indicator), grp in sub.groupby(["Geography", "indicatorname"]):
        grp = grp.sort_values(["_year", "_wave"])
        pts = []
        for _, r in grp.iterrows():
            if pd.isna(r["mean"]):
                continue
            pts.append({
                "wave": str(r["Instrument"]),
                "year": str(r["Year"]),
                "x": f"W{int(r['_wave'])} {str(r['Year'])}" if r["_wave"] else str(r["Year"]),
                "value": round(float(r["mean"]), 4),
                "n": None if pd.isna(r["N"]) else int(r["N"]),
            })
        if pts:
            units = _uniq(grp["units"])[:1]
            series.append({
                "label": f"{country} — {indicator}",
                "country": country,
                "indicator": indicator,
                "units": units[0] if units else "",
                "points": pts,
            })
    return {"series": series, "waves": [], "loaded": True}
