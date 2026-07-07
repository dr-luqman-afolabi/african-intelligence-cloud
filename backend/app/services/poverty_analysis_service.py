from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd


def _weighted_mean(values: pd.Series, weights: pd.Series | None) -> float:
    if weights is None:
        return float(values.mean())
    return float(np.average(values.to_numpy(dtype=float), weights=weights.to_numpy(dtype=float)))


def poverty_headcount(welfare: pd.Series, poverty_line: float, weights: pd.Series | None = None) -> float:
    """FGT(0): share of the population below the poverty line."""
    poor = (welfare < poverty_line).astype(float)
    if weights is None:
        return float(poor.mean())
    return float(np.average(poor.to_numpy(dtype=float), weights=weights.to_numpy(dtype=float)))


def poverty_gap(welfare: pd.Series, poverty_line: float, weights: pd.Series | None = None) -> float:
    """FGT(1): average shortfall from the poverty line, as a share of that line."""
    gap = ((poverty_line - welfare) / poverty_line).clip(lower=0)
    if weights is None:
        return float(gap.mean())
    return float(np.average(gap.to_numpy(dtype=float), weights=weights.to_numpy(dtype=float)))


def squared_poverty_gap(welfare: pd.Series, poverty_line: float, weights: pd.Series | None = None) -> float:
    """FGT(2): poverty severity index, penalizing larger shortfalls more heavily."""
    gap = ((poverty_line - welfare) / poverty_line).clip(lower=0) ** 2
    if weights is None:
        return float(gap.mean())
    return float(np.average(gap.to_numpy(dtype=float), weights=weights.to_numpy(dtype=float)))


def gini_coefficient(welfare: pd.Series, weights: pd.Series | None = None) -> float:
    """Weighted Gini coefficient of inequality, computed from the (weighted) Lorenz curve."""
    values = welfare.to_numpy(dtype=float)
    if weights is None:
        w = np.ones_like(values)
    else:
        w = weights.to_numpy(dtype=float)

    order = np.argsort(values)
    values = values[order]
    w = w[order]

    cum_w = np.cumsum(w)
    cum_wv = np.cumsum(w * values)
    total_w = cum_w[-1]
    total_wv = cum_wv[-1]
    if total_wv == 0 or total_w == 0:
        return 0.0

    lorenz = cum_wv / total_wv
    lorenz_prev = np.concatenate(([0.0], lorenz[:-1]))
    w_share = cum_w / total_w
    w_share_prev = np.concatenate(([0.0], w_share[:-1]))

    area_under_lorenz = np.sum((w_share - w_share_prev) * (lorenz + lorenz_prev) / 2)
    return float(1 - 2 * area_under_lorenz)


def compute_fgt_indices(
    df: pd.DataFrame,
    welfare_variable: str,
    poverty_line: float,
    weight_variable: str | None = None,
) -> dict[str, Any]:
    """Computes the full suite of FGT poverty indices plus inequality and central-tendency stats."""
    welfare = df[welfare_variable].dropna()
    weights = None
    if weight_variable and weight_variable in df.columns:
        weights = df.loc[welfare.index, weight_variable]

    return {
        "headcount": poverty_headcount(welfare, poverty_line, weights),
        "poverty_gap": poverty_gap(welfare, poverty_line, weights),
        "squared_poverty_gap": squared_poverty_gap(welfare, poverty_line, weights),
        "gini": gini_coefficient(welfare, weights),
        "mean_consumption": _weighted_mean(welfare, weights),
        "median_consumption": float(welfare.median()),
        "n_obs": int(len(welfare)),
    }


def compute_grouped_poverty(
    df: pd.DataFrame,
    welfare_variable: str,
    poverty_line: float,
    group_by: str,
    weight_variable: str | None = None,
) -> list[dict[str, Any]]:
    """Computes FGT indices separately for each value of a grouping variable
    (e.g. rural/urban, district, province, gender)."""
    results = []
    for group_value, group_df in df.groupby(group_by, dropna=True):
        stats = compute_fgt_indices(group_df, welfare_variable, poverty_line, weight_variable)
        stats["group"] = str(group_value)
        results.append(stats)
    return sorted(results, key=lambda r: r["headcount"], reverse=True)


def build_charts_payload(overall: dict[str, Any], grouped_results: dict[str, list[dict[str, Any]]]) -> dict[str, Any]:
    """Builds Recharts/Chart.js-ready JSON for the frontend poverty dashboard."""
    charts: dict[str, Any] = {
        "headcount_gauge": {"value": overall["headcount"], "label": "Poverty headcount rate"},
        "gini_gauge": {"value": overall["gini"], "label": "Gini coefficient"},
    }
    for group_name, rows in grouped_results.items():
        charts[f"{group_name}_bar"] = [
            {"group": r["group"], "headcount": r["headcount"], "poverty_gap": r["poverty_gap"]}
            for r in rows
        ]
    return charts


def generate_interpretation(
    overall: dict[str, Any],
    grouped_results: dict[str, list[dict[str, Any]]],
) -> str:
    """Generates a short, AI-ready plain-language interpretation of the poverty results."""
    lines = []
    lines.append(
        f"The poverty headcount rate is {overall['headcount'] * 100:.1f}%, meaning that share of the "
        f"population falls below the specified poverty line, based on {overall['n_obs']:,} observations."
    )
    lines.append(
        f"The poverty gap index is {overall['poverty_gap'] * 100:.1f}%, indicating the average shortfall "
        f"of the poor from the poverty line as a share of that line."
    )
    lines.append(
        f"The squared poverty gap (severity) is {overall['squared_poverty_gap'] * 100:.1f}%, and the Gini "
        f"coefficient of {overall['gini']:.3f} reflects the degree of inequality in the welfare distribution."
    )
    for group_name, rows in grouped_results.items():
        if rows:
            top = rows[0]
            # compute_grouped_poverty labels rows "group"; compute_spatial_poverty labels them
            # "geo_value" — accept either so this works for both poverty and spatial-poverty jobs.
            top_label = top.get("group", top.get("geo_value", "unknown"))
            lines.append(
                f"By {group_name}, poverty is highest in '{top_label}' with a headcount rate of "
                f"{top['headcount'] * 100:.1f}%."
            )
    return " ".join(lines)
