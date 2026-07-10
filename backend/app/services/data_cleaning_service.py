"""Automated data cleaning / modification for AIC Intelligence.

Produces an ordered list of cleaning *steps* (each a small dict the UI can
show and the user can confirm) and applies them to a pandas DataFrame,
returning the cleaned frame plus a human-readable report of what changed.

Supported step kinds:
  - standardize_columns  : trim/normalize column names
  - fix_types            : coerce obviously-numeric object columns to numeric
  - drop_empty           : drop fully-empty rows and columns
  - impute_missing       : fill missing values in target columns (median/mode)
  - drop_missing         : drop rows missing any of the target columns
  - winsorize_outliers   : cap a numeric column at given lower/upper percentiles
  - flag_invalid         : drop rows where a column violates a rule (e.g. < 0)

Free-text cleaning instructions embedded in the user's question are parsed
heuristically into these same steps, so behaviour is transparent and testable.
"""
from __future__ import annotations

import re
from typing import Any

import numpy as np
import pandas as pd


# ---------------------------------------------------------------------------
# Planning
# ---------------------------------------------------------------------------

def plan_cleaning(
    df: pd.DataFrame,
    *,
    target_columns: list[str] | None = None,
    free_text: str | None = None,
    include_safe_basics: bool = True,
    include_missing: bool = True,
    include_outliers: bool = True,
) -> list[dict[str, Any]]:
    """Build an ordered, explainable cleaning plan for ``df``."""
    steps: list[dict[str, Any]] = []
    targets = [c for c in (target_columns or []) if c in df.columns]

    if include_safe_basics:
        steps.append({
            "kind": "standardize_columns",
            "label": "Standardize column names (trim spaces, unify casing)",
        })
        obj_numeric = _numeric_looking_object_cols(df)
        if obj_numeric:
            steps.append({
                "kind": "fix_types",
                "columns": obj_numeric,
                "label": f"Convert {len(obj_numeric)} text column(s) that hold numbers to numeric",
            })
        steps.append({
            "kind": "drop_empty",
            "label": "Drop completely empty rows and columns",
        })

    # Free-text instructions take precedence and may add/override.
    ft_steps = _parse_free_text(free_text or "", df, targets)
    ft_kinds = {s["kind"] for s in ft_steps}

    if include_missing and targets and "impute_missing" not in ft_kinds and "drop_missing" not in ft_kinds:
        missing_targets = [c for c in targets if df[c].isna().any()]
        if missing_targets:
            steps.append({
                "kind": "impute_missing",
                "columns": missing_targets,
                "strategy": "median_or_mode",
                "label": f"Impute missing values in {', '.join(missing_targets)} (median for numbers, mode otherwise)",
            })

    if include_outliers and "winsorize_outliers" not in ft_kinds:
        for c in targets:
            if _is_numeric_like(df, c):
                steps.append({
                    "kind": "winsorize_outliers",
                    "column": c,
                    "lower": 0.01,
                    "upper": 0.99,
                    "label": f"Cap outliers in {c} at the 1st/99th percentile",
                })

    steps.extend(ft_steps)
    return steps


def _numeric_looking_object_cols(df: pd.DataFrame) -> list[str]:
    cols = []
    for c in df.columns:
        if df[c].dtype == object:
            sample = df[c].dropna().astype(str).head(50)
            if len(sample) == 0:
                continue
            ok = sum(bool(re.fullmatch(r"-?\d+(\.\d+)?", s.strip())) for s in sample)
            if ok >= max(1, int(0.8 * len(sample))):
                cols.append(c)
    return cols


def _is_numeric(df: pd.DataFrame, col: str) -> bool:
    return col in df.columns and pd.api.types.is_numeric_dtype(df[col])


def _is_numeric_like(df: pd.DataFrame, col: str) -> bool:
    """True if a column is numeric, or text that will become numeric after fix_types."""
    if _is_numeric(df, col):
        return True
    if col in df.columns and df[col].dtype == object:
        sample = df[col].dropna().astype(str).head(50)
        if len(sample) == 0:
            return False
        ok = sum(bool(re.fullmatch(r"-?\d+(\.\d+)?", x.strip())) for x in sample)
        return ok >= max(1, int(0.8 * len(sample)))
    return False


def _parse_free_text(text: str, df: pd.DataFrame, targets: list[str]) -> list[dict[str, Any]]:
    """Heuristically turn a natural-language cleaning instruction into steps."""
    steps: list[dict[str, Any]] = []
    t = text.lower()
    if not t:
        return steps

    # "cap outliers at the 99th percentile" / "winsorize at 95%"
    m = re.search(r"(?:cap|winsoriz\w*|clip)\D*(\d{1,2}(?:\.\d+)?)\s*(?:th|st|nd|rd)?\s*(?:percentile|%|pct)", t)
    if m:
        upper = min(0.999, float(m.group(1)) / 100.0)
        for c in targets:
            if _is_numeric_like(df, c):
                steps.append({
                    "kind": "winsorize_outliers", "column": c,
                    "lower": round(1 - upper, 4), "upper": round(upper, 4),
                    "label": f"Cap outliers in {c} at the {m.group(1)}th percentile (from your instruction)",
                })

    # "drop rows with no/missing consumption" / "remove households missing X"
    if re.search(r"\b(drop|remove|exclude)\b.*\b(missing|no|without|empty|blank)\b", t):
        cols = [c for c in df.columns if c.lower() in t] or targets
        cols = [c for c in cols if c in df.columns]
        if cols:
            steps.append({
                "kind": "drop_missing", "columns": cols,
                "label": f"Drop rows missing {', '.join(cols)} (from your instruction)",
            })

    # "drop negative consumption" / "remove negative values"
    if re.search(r"\bnegative\b", t) and re.search(r"\b(drop|remove|exclude)\b", t):
        cols = [c for c in df.columns if c.lower() in t] or targets
        for c in cols:
            if _is_numeric_like(df, c):
                steps.append({
                    "kind": "flag_invalid", "column": c, "op": "lt", "value": 0,
                    "label": f"Drop rows where {c} is negative (from your instruction)",
                })
    return steps


# ---------------------------------------------------------------------------
# Application
# ---------------------------------------------------------------------------

def apply_cleaning(df: pd.DataFrame, steps: list[dict[str, Any]]) -> tuple[pd.DataFrame, list[str]]:
    """Apply cleaning ``steps`` in order. Returns (cleaned_df, report_lines)."""
    df = df.copy()
    report: list[str] = []
    start_rows = len(df)

    for step in steps or []:
        kind = step.get("kind")
        try:
            if kind == "standardize_columns":
                new_cols = {c: re.sub(r"\s+", "_", str(c).strip()) for c in df.columns}
                changed = sum(1 for k, v in new_cols.items() if k != v)
                df = df.rename(columns=new_cols)
                if changed:
                    report.append(f"Standardized {changed} column name(s).")

            elif kind == "fix_types":
                for c in step.get("columns", []):
                    if c in df.columns:
                        df[c] = pd.to_numeric(df[c], errors="coerce")
                report.append(f"Converted {len(step.get('columns', []))} column(s) to numeric.")

            elif kind == "drop_empty":
                before = df.shape
                df = df.dropna(axis=0, how="all").dropna(axis=1, how="all")
                if df.shape != before:
                    report.append(
                        f"Dropped {before[0]-df.shape[0]} empty row(s) and {before[1]-df.shape[1]} empty column(s)."
                    )

            elif kind == "impute_missing":
                for c in step.get("columns", []):
                    if c not in df.columns:
                        continue
                    n = int(df[c].isna().sum())
                    if n == 0:
                        continue
                    if pd.api.types.is_numeric_dtype(df[c]):
                        fill = df[c].median()
                    else:
                        mode = df[c].mode(dropna=True)
                        fill = mode.iloc[0] if len(mode) else ""
                    df[c] = df[c].fillna(fill)
                    report.append(f"Imputed {n} missing value(s) in {c}.")

            elif kind == "drop_missing":
                cols = [c for c in step.get("columns", []) if c in df.columns]
                if cols:
                    before = len(df)
                    df = df.dropna(subset=cols)
                    report.append(f"Dropped {before-len(df)} row(s) missing {', '.join(cols)}.")

            elif kind == "winsorize_outliers":
                c = step.get("column")
                if c in df.columns and pd.api.types.is_numeric_dtype(df[c]):
                    lo = df[c].quantile(float(step.get("lower", 0.01)))
                    hi = df[c].quantile(float(step.get("upper", 0.99)))
                    capped = int(((df[c] < lo) | (df[c] > hi)).sum())
                    df[c] = df[c].clip(lower=lo, upper=hi)
                    if capped:
                        report.append(f"Capped {capped} outlier(s) in {c}.")

            elif kind == "flag_invalid":
                c = step.get("column")
                if c in df.columns and pd.api.types.is_numeric_dtype(df[c]):
                    op = step.get("op", "lt")
                    val = step.get("value", 0)
                    before = len(df)
                    if op == "lt":
                        df = df[~(df[c] < val)]
                    elif op == "gt":
                        df = df[~(df[c] > val)]
                    report.append(f"Removed {before-len(df)} invalid row(s) in {c}.")
        except Exception as exc:  # never let one step abort the whole clean
            report.append(f"Skipped a cleaning step ({kind}) due to: {exc}")

    df = df.reset_index(drop=True)
    if not report:
        report.append("No changes were necessary — data already met the checks.")
    report.append(f"Rows: {start_rows} -> {len(df)}.")
    return df, report
