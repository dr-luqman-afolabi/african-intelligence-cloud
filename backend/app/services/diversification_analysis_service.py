"""Diversification analytics engine — crop, income, and livelihood diversity
indices computed from LSMS-family survey microdata.

Diversification indices (Simpson, Shannon, Herfindahl) are fundamentally
computed over a set of per-source value/count columns (e.g. one column per
crop, or per income source) — the fixed StandardConcept vocabulary only has
single aggregate concepts (crop_value, livestock), not a per-crop breakdown,
so this engine takes the source columns directly in the request rather than
through variable mapping. This mirrors how welfare_variable/geo_variable are
already passed directly to the poverty/spatial endpoints.
"""
from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd


def _row_shares(df: pd.DataFrame, columns: list[str]) -> pd.DataFrame:
    """Per-row (household) share of each source column, clipped to >= 0 and
    normalised to sum to 1 across the given columns. Rows where every source
    is zero/missing are dropped (undefined diversification for that row)."""
    values = df[columns].apply(pd.to_numeric, errors="coerce").fillna(0).clip(lower=0)
    totals = values.sum(axis=1)
    valid = totals > 0
    shares = values.loc[valid].div(totals.loc[valid], axis=0)
    return shares


def simpson_index(shares_row: pd.Series) -> float:
    """Simpson's diversity index: 1 - sum(p_i^2). 0 = no diversity (one
    source dominates), approaches 1 as sources become more even/numerous."""
    return float(1 - np.sum(shares_row.to_numpy(dtype=float) ** 2))


def shannon_index(shares_row: pd.Series) -> float:
    """Shannon entropy index: -sum(p_i * ln(p_i)). 0 = no diversity, higher
    values indicate more even distribution across more sources."""
    p = shares_row.to_numpy(dtype=float)
    p = p[p > 0]
    if len(p) == 0:
        return 0.0
    return float(-np.sum(p * np.log(p)))


def herfindahl_index(shares_row: pd.Series) -> float:
    """Herfindahl-Hirschman concentration index: sum(p_i^2). Inverse of
    diversity — 1 = fully concentrated in one source, approaches 0 as sources
    become more even/numerous."""
    return float(np.sum(shares_row.to_numpy(dtype=float) ** 2))


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


def _diversity_stats_for_sources(
    df: pd.DataFrame, columns: list[str], weights: pd.Series | None
) -> dict[str, Any] | None:
    """Household-level Simpson/Shannon/Herfindahl over `columns`, aggregated
    to a population-weighted mean. Returns None if fewer than 2 usable
    source columns are present (diversification is undefined over 1 source)."""
    present = [c for c in columns if c in df.columns]
    if len(present) < 2:
        return None

    shares = _row_shares(df, present)
    if len(shares) == 0:
        return None

    source_count = (shares > 0).sum(axis=1)
    simpson = shares.apply(simpson_index, axis=1)
    shannon = shares.apply(shannon_index, axis=1)
    herfindahl = shares.apply(herfindahl_index, axis=1)

    w = weights.loc[shares.index].dropna() if weights is not None else None
    return {
        "source_count": _weighted_mean(source_count, w),
        "simpson_index": _weighted_mean(simpson, w),
        "shannon_index": _weighted_mean(shannon, w),
        "herfindahl_index": _weighted_mean(herfindahl, w),
        "n_obs": int(len(shares)),
    }


def compute_diversification_stats(
    df: pd.DataFrame,
    crop_columns: list[str] | None = None,
    income_columns: list[str] | None = None,
    livelihood_columns: list[str] | None = None,
    livestock_columns: list[str] | None = None,
    weight_variable: str | None = None,
) -> dict[str, Any]:
    """Computes diversification indices for one or more source-column groups.
    Each group is independent — a request can supply any subset. `crop_count`
    in the response is the crop group's source_count (renamed for clarity
    since that's the term used in the product spec)."""
    weights = df[weight_variable] if weight_variable and weight_variable in df.columns else None
    stats: dict[str, Any] = {"n_obs": int(len(df))}

    if crop_columns:
        crop = _diversity_stats_for_sources(df, crop_columns, weights)
        if crop:
            stats["crop_count"] = crop["source_count"]
            stats["crop_simpson_index"] = crop["simpson_index"]
            stats["crop_shannon_index"] = crop["shannon_index"]
            stats["crop_herfindahl_index"] = crop["herfindahl_index"]

    if income_columns:
        income = _diversity_stats_for_sources(df, income_columns, weights)
        if income:
            stats["income_diversification_simpson"] = income["simpson_index"]
            stats["income_diversification_shannon"] = income["shannon_index"]

    if livelihood_columns:
        livelihood = _diversity_stats_for_sources(df, livelihood_columns, weights)
        if livelihood:
            stats["livelihood_diversification_simpson"] = livelihood["simpson_index"]
            stats["livelihood_diversification_shannon"] = livelihood["shannon_index"]

    if livestock_columns:
        livestock = _diversity_stats_for_sources(df, livestock_columns, weights)
        if livestock:
            stats["livestock_diversification_simpson"] = livestock["simpson_index"]
            stats["livestock_diversification_shannon"] = livestock["shannon_index"]

    return stats


def compute_grouped_diversification(
    df: pd.DataFrame,
    group_by: str,
    crop_columns: list[str] | None = None,
    income_columns: list[str] | None = None,
    livelihood_columns: list[str] | None = None,
    livestock_columns: list[str] | None = None,
    weight_variable: str | None = None,
) -> list[dict[str, Any]]:
    """Diversification stats computed separately for each value of a
    grouping variable (e.g. district, province, urban/rural)."""
    results = []
    for group_value, group_df in df.groupby(group_by, dropna=True):
        stats = compute_diversification_stats(
            group_df, crop_columns, income_columns, livelihood_columns, livestock_columns, weight_variable
        )
        stats["group"] = str(group_value)
        results.append(stats)
    return sorted(
        results,
        key=lambda r: r.get("crop_simpson_index") if r.get("crop_simpson_index") is not None else -1,
        reverse=True,
    )


def compute_spatial_diversification(
    df: pd.DataFrame,
    geo_variable: str,
    crop_columns: list[str] | None = None,
    income_columns: list[str] | None = None,
    livelihood_columns: list[str] | None = None,
    livestock_columns: list[str] | None = None,
    weight_variable: str | None = None,
) -> list[dict[str, Any]]:
    """Diversification stats per geographic unit, in the
    {..., "geo_value": ...} shape
    spatial_analysis_service.merge_stats_with_geojson() expects."""
    results = []
    for geo_value, geo_df in df.groupby(geo_variable, dropna=True):
        stats = compute_diversification_stats(
            geo_df, crop_columns, income_columns, livelihood_columns, livestock_columns, weight_variable
        )
        stats["geo_value"] = str(geo_value)
        results.append(stats)
    return sorted(
        results,
        key=lambda r: r.get("crop_simpson_index") if r.get("crop_simpson_index") is not None else -1,
        reverse=True,
    )


def build_diversification_charts_payload(
    overall: dict[str, Any], grouped_results: dict[str, list[dict[str, Any]]]
) -> dict[str, Any]:
    """Recharts-ready JSON for the diversification dashboard."""
    charts: dict[str, Any] = {}
    if overall.get("crop_simpson_index") is not None:
        charts["crop_diversity_gauge"] = {"value": overall["crop_simpson_index"], "label": "Crop diversity (Simpson)"}
    for group_name, rows in grouped_results.items():
        charts[f"{group_name}_bar"] = [
            {"group": r["group"], "crop_simpson_index": r.get("crop_simpson_index"), "crop_count": r.get("crop_count")}
            for r in rows
        ]
    return charts


def generate_diversification_interpretation(
    overall: dict[str, Any], grouped_results: dict[str, list[dict[str, Any]]]
) -> str:
    """Short plain-language interpretation of the diversification results."""
    lines = []
    if overall.get("crop_count") is not None:
        lines.append(
            f"Households grow an average of {overall['crop_count']:.1f} distinct crops "
            f"(Simpson diversity index {overall.get('crop_simpson_index', 0):.2f}, "
            f"Shannon index {overall.get('crop_shannon_index', 0):.2f})."
        )
    if overall.get("income_diversification_simpson") is not None:
        lines.append(f"Income diversification (Simpson index) is {overall['income_diversification_simpson']:.2f}.")
    if overall.get("livelihood_diversification_simpson") is not None:
        lines.append(
            f"Livelihood diversification (Simpson index) is {overall['livelihood_diversification_simpson']:.2f}."
        )
    if overall.get("livestock_diversification_simpson") is not None:
        lines.append(
            f"Livestock diversification (Simpson index) is {overall['livestock_diversification_simpson']:.2f}."
        )
    for group_name, rows in grouped_results.items():
        top = next((r for r in rows if r.get("crop_simpson_index") is not None), None)
        if top:
            lines.append(
                f"By {group_name}, crop diversity is highest in '{top['group']}' "
                f"(Simpson index {top['crop_simpson_index']:.2f})."
            )
    return " ".join(lines) if lines else "Not enough source columns supplied to generate an interpretation."
