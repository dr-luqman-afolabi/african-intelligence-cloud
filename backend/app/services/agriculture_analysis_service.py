"""Agriculture analytics engine — household/plot-level farm productivity and
input-adoption statistics computed from LSMS-family survey microdata.

Mirrors poverty_analysis_service.py's structure: weighted-mean primitives,
an overall compute_* function, a grouped variant, and chart/interpretation
builders. Inputs are resolved through VariableMapping standard concepts
(land_area, crop_output, crop_value, livestock, fertilizer, improved_seed,
irrigation, extension) rather than hardcoded survey-specific column names.

Caveats documented inline: the standard-concept vocabulary doesn't include a
dedicated labor-hours or livestock-value concept, so labour_productivity uses
household_size as a labor-availability proxy, and livestock_income reports
whatever the mapped "livestock" column holds (a head-count survey will yield
livestock holdings, not currency income — callers should treat the field
name loosely for those surveys).
"""
from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd


def _weighted_mean(values: pd.Series, weights: pd.Series | None) -> float | None:
    values = values.dropna()
    if len(values) == 0:
        return None
    if weights is None:
        return float(values.mean())
    w = weights.loc[values.index].dropna()
    values = values.loc[w.index]
    if len(values) == 0:
        return None
    return float(np.average(values.to_numpy(dtype=float), weights=w.to_numpy(dtype=float)))


def _adoption_rate(series: pd.Series, weights: pd.Series | None) -> float | None:
    """Share of households "adopting" an input. Handles boolean-like 0/1
    columns, yes/no strings, and continuous quantities (any positive value
    counts as adoption)."""
    series = series.dropna()
    if len(series) == 0:
        return None
    if series.dtype == object:
        adopted = series.astype(str).str.strip().str.lower().isin(
            {"yes", "y", "true", "1"}
        ).astype(float)
    else:
        adopted = (pd.to_numeric(series, errors="coerce") > 0).astype(float)
    w = weights.loc[adopted.index].dropna() if weights is not None else None
    return _weighted_mean(adopted, w)


def compute_agriculture_stats(
    df: pd.DataFrame,
    mapping: dict[str, str],
    weight_variable: str | None = None,
) -> dict[str, Any]:
    """Computes farm productivity and input-adoption statistics for one group
    of households. `mapping` is {standard_concept: raw_column_name} — only
    concepts present both in `mapping` and `df.columns` are computed; the
    rest are omitted (not zeroed) so missing survey modules are visible as
    missing, not misleadingly reported as zero."""
    weights = df[weight_variable] if weight_variable and weight_variable in df.columns else None

    stats: dict[str, Any] = {"n_obs": int(len(df))}

    land = df[mapping["land_area"]] if "land_area" in mapping and mapping["land_area"] in df.columns else None
    crop_output = df[mapping["crop_output"]] if "crop_output" in mapping and mapping["crop_output"] in df.columns else None
    crop_value = df[mapping["crop_value"]] if "crop_value" in mapping and mapping["crop_value"] in df.columns else None
    livestock = df[mapping["livestock"]] if "livestock" in mapping and mapping["livestock"] in df.columns else None
    hh_size = df[mapping["household_size"]] if "household_size" in mapping and mapping["household_size"] in df.columns else None

    if crop_output is not None and land is not None:
        with np.errstate(divide="ignore", invalid="ignore"):
            yield_series = (crop_output / land.replace(0, np.nan)).replace([np.inf, -np.inf], np.nan)
        stats["crop_yield"] = _weighted_mean(yield_series, weights)

    if crop_value is not None:
        stats["value_of_production"] = _weighted_mean(crop_value, weights)
        stats["crop_income"] = stats["value_of_production"]
        stats["market_participation_rate"] = _adoption_rate(crop_value, weights)

    if crop_value is not None and land is not None:
        with np.errstate(divide="ignore", invalid="ignore"):
            land_prod = (crop_value / land.replace(0, np.nan)).replace([np.inf, -np.inf], np.nan)
        stats["land_productivity"] = _weighted_mean(land_prod, weights)

    if crop_value is not None and hh_size is not None:
        with np.errstate(divide="ignore", invalid="ignore"):
            labour_prod = (crop_value / hh_size.replace(0, np.nan)).replace([np.inf, -np.inf], np.nan)
        stats["labour_productivity"] = _weighted_mean(labour_prod, weights)

    if livestock is not None:
        stats["livestock_income"] = _weighted_mean(livestock, weights)

    for concept, key in (
        ("fertilizer", "fertilizer_adoption_rate"),
        ("improved_seed", "improved_seed_adoption_rate"),
        ("irrigation", "irrigation_access_rate"),
        ("extension", "extension_access_rate"),
    ):
        if concept in mapping and mapping[concept] in df.columns:
            stats[key] = _adoption_rate(df[mapping[concept]], weights)

    return stats


def compute_grouped_agriculture(
    df: pd.DataFrame,
    mapping: dict[str, str],
    group_by: str,
    weight_variable: str | None = None,
) -> list[dict[str, Any]]:
    """Agriculture stats computed separately for each value of a grouping
    variable (e.g. district, province, gender of household head)."""
    results = []
    for group_value, group_df in df.groupby(group_by, dropna=True):
        stats = compute_agriculture_stats(group_df, mapping, weight_variable)
        stats["group"] = str(group_value)
        results.append(stats)
    return sorted(
        results,
        key=lambda r: r.get("crop_yield") if r.get("crop_yield") is not None else -1,
        reverse=True,
    )


def compute_spatial_agriculture(
    df: pd.DataFrame,
    mapping: dict[str, str],
    geo_variable: str,
    weight_variable: str | None = None,
) -> list[dict[str, Any]]:
    """Agriculture stats per geographic unit, in the {..., "geo_value": ...}
    shape spatial_analysis_service.merge_stats_with_geojson() expects."""
    results = []
    for geo_value, geo_df in df.groupby(geo_variable, dropna=True):
        stats = compute_agriculture_stats(geo_df, mapping, weight_variable)
        stats["geo_value"] = str(geo_value)
        results.append(stats)
    return sorted(
        results,
        key=lambda r: r.get("crop_yield") if r.get("crop_yield") is not None else -1,
        reverse=True,
    )


def build_agriculture_charts_payload(
    overall: dict[str, Any], grouped_results: dict[str, list[dict[str, Any]]]
) -> dict[str, Any]:
    """Recharts-ready JSON for the agriculture dashboard."""
    charts: dict[str, Any] = {}
    if overall.get("crop_yield") is not None:
        charts["crop_yield_gauge"] = {"value": overall["crop_yield"], "label": "Crop yield"}
    adoption_keys = [
        ("fertilizer_adoption_rate", "Fertilizer"),
        ("improved_seed_adoption_rate", "Improved seed"),
        ("irrigation_access_rate", "Irrigation"),
        ("extension_access_rate", "Extension"),
    ]
    charts["input_adoption_bar"] = [
        {"input": label, "adoption_rate": overall[key]}
        for key, label in adoption_keys
        if overall.get(key) is not None
    ]
    for group_name, rows in grouped_results.items():
        charts[f"{group_name}_bar"] = [
            {
                "group": r["group"],
                "crop_yield": r.get("crop_yield"),
                "land_productivity": r.get("land_productivity"),
            }
            for r in rows
        ]
    return charts


def generate_agriculture_interpretation(
    overall: dict[str, Any], grouped_results: dict[str, list[dict[str, Any]]]
) -> str:
    """Short plain-language interpretation of the agriculture results."""
    lines = []
    if overall.get("crop_yield") is not None:
        lines.append(
            f"Mean crop yield is {overall['crop_yield']:.2f} units of output per unit of land, "
            f"based on {overall['n_obs']:,} farm households."
        )
    if overall.get("land_productivity") is not None:
        lines.append(f"Land productivity (value of production per unit area) is {overall['land_productivity']:.2f}.")
    adoption_bits = []
    for key, label in (
        ("fertilizer_adoption_rate", "fertilizer"),
        ("improved_seed_adoption_rate", "improved seed"),
        ("irrigation_access_rate", "irrigation"),
        ("extension_access_rate", "extension services"),
    ):
        if overall.get(key) is not None:
            adoption_bits.append(f"{label} ({overall[key] * 100:.1f}%)")
    if adoption_bits:
        lines.append("Input adoption rates: " + ", ".join(adoption_bits) + ".")
    if overall.get("market_participation_rate") is not None:
        lines.append(f"Market participation rate is {overall['market_participation_rate'] * 100:.1f}%.")
    for group_name, rows in grouped_results.items():
        top = next((r for r in rows if r.get("crop_yield") is not None), None)
        if top:
            lines.append(
                f"By {group_name}, crop yield is highest in '{top['group']}' at {top['crop_yield']:.2f}."
            )
    return " ".join(lines) if lines else "Not enough mapped agriculture variables to generate an interpretation."
