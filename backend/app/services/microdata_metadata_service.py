from __future__ import annotations

import io
import os
import re
import logging
import tempfile
from typing import Any

import pandas as pd

logger = logging.getLogger(__name__)

COUNTRY_HINTS = {
    "rwanda": "RWA", "rwa": "RWA",
    "nigeria": "NGA", "nga": "NGA",
    "kenya": "KEN", "ken": "KEN",
    "uganda": "UGA", "uga": "UGA",
    "tanzania": "TZA", "tza": "TZA",
    "ghana": "GHA", "gha": "GHA",
    "ethiopia": "ETH", "eth": "ETH",
    "senegal": "SEN", "sen": "SEN",
    "malawi": "MWI", "mwi": "MWI",
    "zambia": "ZMB", "zmb": "ZMB",
}

SERIES_HINTS = ["eicv", "unps", "dhs", "lsms", "mics", "afrobarometer", "gmd", "hies"]


def _detect_country(text: str) -> str | None:
    lowered = text.lower()
    for key, iso3 in COUNTRY_HINTS.items():
        if key in lowered:
            return iso3
    return None


def _detect_series(text: str) -> str | None:
    lowered = text.lower()
    for series in SERIES_HINTS:
        if series in lowered:
            return series.upper()
    return None


def _detect_year(text: str) -> int | None:
    matches = re.findall(r"(?:19|20)\d{2}", text)
    years = [int(y) for y in matches]
    plausible = [y for y in years if 1990 <= y <= 2035]
    if plausible:
        return plausible[-1]
    return None


def load_dataframe(content: bytes, file_extension: str) -> tuple[pd.DataFrame, dict[str, Any]]:
    """Loads a microdata file into a pandas DataFrame plus variable metadata (labels, value labels).

    Supports .csv, .xlsx, .dta (Stata) and .sav (SPSS), the latter two via pyreadstat.
    """
    meta: dict[str, Any] = {"column_labels": {}, "value_labels": {}}
    buffer = io.BytesIO(content)

    if file_extension == "csv":
        df = pd.read_csv(buffer)
    elif file_extension == "xlsx":
        df = pd.read_excel(buffer)
    elif file_extension in ("dta", "sav"):
        import pyreadstat
        tmp_path = None
        with tempfile.NamedTemporaryFile(suffix=f".{file_extension}", delete=False) as tmp:
            tmp.write(content)
            tmp_path = tmp.name
        try:
            reader = pyreadstat.read_dta if file_extension == "dta" else pyreadstat.read_sav
            df, rs_meta = reader(tmp_path)
            meta["column_labels"] = dict(zip(rs_meta.column_names, rs_meta.column_labels))
            meta["value_labels"] = rs_meta.variable_value_labels or {}
        finally:
            if tmp_path:
                try:
                    os.unlink(tmp_path)
                except OSError:
                    pass
    else:
        raise ValueError(f"Unsupported file extension: {file_extension}")

    return df, meta


def extract_metadata(content: bytes, file_extension: str, original_filename: str) -> dict[str, Any]:
    """Extracts dataset- and variable-level metadata used to populate MicrodataDataset/MicrodataVariable rows."""
    df, meta = load_dataframe(content, file_extension)

    row_count = int(len(df))
    column_count = int(len(df.columns))
    missing_cells = int(df.isna().sum().sum())

    detected_country = _detect_country(original_filename)
    detected_series = _detect_series(original_filename)
    detected_year = _detect_year(original_filename)

    variables = []
    for idx, column in enumerate(df.columns):
        series = df[column]
        variables.append({
            "variable_name": str(column),
            "variable_label": meta["column_labels"].get(column),
            "value_labels": meta["value_labels"].get(column),
            "variable_index": idx,
            "inferred_dtype": str(series.dtype),
            "missing_count": int(series.isna().sum()),
        })

    return {
        "row_count": row_count,
        "column_count": column_count,
        "missing_cells": missing_cells,
        "file_type": file_extension,
        "detected_country": detected_country,
        "detected_series": detected_series,
        "detected_year": detected_year,
        "variables": variables,
    }
