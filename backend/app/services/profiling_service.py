import time
import logging
from pathlib import Path
from typing import Any

import pandas as pd
import numpy as np

logger = logging.getLogger(__name__)


def _safe_scalar(val: Any) -> Any:
    """Convert numpy scalars to Python natives so they serialise to JSON."""
    if isinstance(val, (np.integer,)):
        return int(val)
    if isinstance(val, (np.floating,)):
        return float(val) if not np.isnan(val) else None
    return val


def load_dataframe(storage_path: str, extension: str) -> pd.DataFrame:
    """Load a supported file into a pandas DataFrame."""
    path = Path(storage_path)
    ext = extension.lower()
    if ext == "csv":
        return pd.read_csv(path, low_memory=False)
    if ext in ("xlsx", "xls"):
        return pd.read_excel(path, engine="openpyxl")
    if ext == "json":
        return pd.read_json(path)
    if ext == "parquet":
        return pd.read_parquet(path)
    raise ValueError(f"Cannot profile file with extension '.{ext}'")


def profile_dataframe(df: pd.DataFrame) -> dict:
    """Compute dataset-level and column-level statistics."""
    start = time.monotonic()

    row_count = len(df)
    col_count = len(df.columns)
    missing_cells = int(df.isnull().sum().sum())
    missing_pct = round(missing_cells / max(row_count * col_count, 1) * 100, 2)
    duplicate_rows = int(df.duplicated().sum())

    numeric_cols = int(df.select_dtypes(include=[np.number]).shape[1])
    datetime_cols = int(df.select_dtypes(include=["datetime", "datetimetz"]).shape[1])
    categorical_cols = col_count - numeric_cols - datetime_cols

    columns = []
    for idx, col in enumerate(df.columns):
        series = df[col]
        null_count = int(series.isnull().sum())
        unique_count = int(series.nunique(dropna=True))
        dtype_str = str(series.dtype)
        sample_values = [_safe_scalar(v) for v in series.dropna().head(5).tolist()]

        col_meta: dict = {
            "column_name": str(col),
            "column_index": idx,
            "inferred_dtype": dtype_str,
            "null_count": null_count,
            "unique_count": unique_count,
            "sample_values": sample_values,
            "min_value": None,
            "max_value": None,
            "mean_value": None,
        }

        if pd.api.types.is_numeric_dtype(series):
            non_null = series.dropna()
            if len(non_null) > 0:
                col_meta["min_value"] = str(_safe_scalar(non_null.min()))
                col_meta["max_value"] = str(_safe_scalar(non_null.max()))
                col_meta["mean_value"] = _safe_scalar(non_null.mean())

        columns.append(col_meta)

    duration_ms = int((time.monotonic() - start) * 1000)

    return {
        "summary": {
            "row_count": row_count,
            "column_count": col_count,
            "missing_cells": missing_cells,
            "missing_cells_pct": missing_pct,
            "duplicate_rows": duplicate_rows,
            "numeric_columns": numeric_cols,
            "categorical_columns": categorical_cols,
            "datetime_columns": datetime_cols,
            "profiling_duration_ms": duration_ms,
        },
        "columns": columns,
    }


def run_profiling(storage_path: str, extension: str) -> dict:
    """Load file and run profiling. Returns profile dict or raises on failure."""
    logger.info("Starting profiling", extra={"path": storage_path})
    df = load_dataframe(storage_path, extension)
    result = profile_dataframe(df)
    logger.info(
        "Profiling complete",
        extra={
            "rows": result["summary"]["row_count"],
            "cols": result["summary"]["column_count"],
            "duration_ms": result["summary"]["profiling_duration_ms"],
        },
    )
    return result
