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


# Complete EPAR LSMS-ISA dissemination catalog. Packages remain at the
# authoritative BSD-3-Clause source and are exposed through AIC with immutable
# provenance metadata. The aggregate indicator file loaded above covers all of
# these waves; the packages provide the analysis-ready final_data tables and
# the intermediate construction tables needed for reproducibility.
_REPOSITORY = "EvansSchoolPolicyAnalysisAndResearch/LSMS-Data-Dissemination"
_SOURCE_COMMIT = "73f0ba6c4425057039d4d69388db6103320a5ccc"
_PACKAGE_ROWS = [
    ("eth_ess_w1", "Ethiopia ESS", "ETH", "Wave 1", "2011-12", "Ethiopia ESS/Ethiopia ESS W1.zip", 13015522),
    ("eth_ess_w2", "Ethiopia ESS", "ETH", "Wave 2", "2013-14", "Ethiopia ESS/Ethiopia ESS W2.zip", 19400218),
    ("eth_ess_w3", "Ethiopia ESS", "ETH", "Wave 3", "2015-16", "Ethiopia ESS/Ethiopia ESS W3.zip", 22567589),
    ("eth_ess_w4", "Ethiopia ESS", "ETH", "Wave 4", "2018-19", "Ethiopia ESS/Ethiopia ESS W4.zip", 15472589),
    ("eth_ess_w5", "Ethiopia ESS", "ETH", "Wave 5", "2021-22", "Ethiopia ESS/Ethiopia ESS W5.zip", 12969323),
    ("nga_ghs_w1", "Nigeria GHS", "NGA", "Wave 1", "2010-11", "Nigeria GHS/Nigeria GHS W1.zip", 10358259),
    ("nga_ghs_w2", "Nigeria GHS", "NGA", "Wave 2", "2012-13", "Nigeria GHS/Nigeria GHS W2.zip", 10670643),
    ("nga_ghs_w3", "Nigeria GHS", "NGA", "Wave 3", "2015-16", "Nigeria GHS/Nigeria GHS W3.zip", 13699670),
    ("nga_ghs_w4", "Nigeria GHS", "NGA", "Wave 4", "2018-19", "Nigeria GHS/Nigeria GHS W4.zip", 15190078),
    ("nga_ghs_w5", "Nigeria GHS", "NGA", "Wave 5", "2022-23", "Nigeria GHS/Nigeria GHS W5.zip", 18709655),
    ("tza_nps_w1", "Tanzania NPS", "TZA", "Wave 1", "2008-09", "Tanzania NPS/Tanzania NPS W1.zip", 8306627),
    ("tza_nps_w2", "Tanzania NPS", "TZA", "Wave 2", "2010-11", "Tanzania NPS/Tanzania NPS W2.zip", 9505936),
    ("tza_nps_w3", "Tanzania NPS", "TZA", "Wave 3", "2012-13", "Tanzania NPS/Tanzania NPS W3.zip", 10621711),
    ("tza_nps_w4", "Tanzania NPS", "TZA", "Wave 4", "2014-15", "Tanzania NPS/Tanzania NPS W4.zip", 7653509),
    ("tza_nps_sdd", "Tanzania NPS", "TZA", "SDD", "2019-20", "Tanzania NPS/Tanzania NPS SDD.zip", 3408896),
    ("tza_nps_w5", "Tanzania NPS", "TZA", "Wave 5", "2020-21", "Tanzania NPS/Tanzania NPS W5.zip", 11001704),
    ("mwi_ihs_w1", "Malawi IHS", "MWI", "Wave 1", "2010-11", "Malawi IHS/MWI IHS W1.zip", 34844151),
    ("mwi_ihps_w2", "Malawi IHS", "MWI", "Wave 2", "2013", "Malawi IHS/MWI IHPS W2.zip", 13286429),
    ("mwi_ihs_w3", "Malawi IHS", "MWI", "Wave 3", "2016-17", "Malawi IHS/MWI IHS IHPS W3.zip", 36960585),
    ("mwi_ihs_w4", "Malawi IHS", "MWI", "Wave 4", "2019-20", "Malawi IHS/MWI IHS IHPS W4.zip", 46251157),
    ("uga_unps_w1", "Uganda UNPS", "UGA", "Wave 1", "2009-10", "Uganda UNPS/Uganda UNPS W1.zip", 9945062),
    ("uga_unps_w2", "Uganda UNPS", "UGA", "Wave 2", "2010-11", "Uganda UNPS/Uganda UNPS W2.zip", 11141083),
    ("uga_unps_w3", "Uganda UNPS", "UGA", "Wave 3", "2011-12", "Uganda UNPS/Uganda UNPS W3.zip", 13202164),
    ("uga_unps_w4", "Uganda UNPS", "UGA", "Wave 4", "2013-14", "Uganda UNPS/Uganda UNPS W4.zip", 17682073),
    ("uga_unps_w5", "Uganda UNPS", "UGA", "Wave 5", "2015-16", "Uganda UNPS/Uganda UNPS W5.zip", 12049821),
    ("uga_unps_w7", "Uganda UNPS", "UGA", "Wave 7", "2018-19", "Uganda UNPS/Uganda UNPS W7.zip", 14980655),
    ("uga_unps_w8", "Uganda UNPS", "UGA", "Wave 8", "2019-20", "Uganda UNPS/Uganda UNPS W8.zip", 15141380),
]


def get_packages() -> dict[str, Any]:
    """Return every source wave with a commit-pinned download URL.

    Pinning the SHA prevents an upstream update from silently changing a
    research input. Each ZIP includes EPAR's complete created_data and
    analysis-ready final_data directories for that wave.
    """
    from urllib.parse import quote

    packages = []
    for package_id, programme, country, wave, years, path, size_bytes in _PACKAGE_ROWS:
        encoded_path = quote(path, safe="/")
        packages.append({
            "id": package_id,
            "programme": programme,
            "country_iso3": country,
            "wave": wave,
            "years": years,
            "file_name": path.rsplit("/", 1)[-1],
            "size_bytes": size_bytes,
            "download_url": f"https://raw.githubusercontent.com/{_REPOSITORY}/{_SOURCE_COMMIT}/{encoded_path}",
            "source_path": path,
        })
    return {
        "source": "EPAR LSMS Data Dissemination",
        "repository": f"https://github.com/{_REPOSITORY}",
        "source_commit": _SOURCE_COMMIT,
        "license": "BSD-3-Clause",
        "package_count": len(packages),
        "countries": sorted({p[2] for p in _PACKAGE_ROWS}),
        "packages": packages,
    }
