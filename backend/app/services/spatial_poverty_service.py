"""Spatial poverty analysis service (SCAFFOLD).

Not wired into main.py yet. See MICRODATA_GIS_FEATURE_PLAN.md before enabling
this feature. Poverty indicators derived from DHS/UNPS/EICV uploads must be
aggregated to admin-boundary level before any geometry join, so respondent-
level data is never mapped or exposed to the frontend.
"""
from __future__ import annotations

from typing import Any
import pandas as pd

GEOPANDAS_AVAILABLE = False


def load_admin_boundaries(country_iso3: str, admin_level: int = 1) -> Any:
  raise NotImplementedError("scaffold stub: wire up a real GADM/HDX boundary source before use.")

def aggregate_microdata_to_boundaries(microdata: pd.DataFrame, boundary_column: str, value_column: str) -> pd.DataFrame:
  grouped = microdata.groupby(boundary_column)[value_column]
  summary = grouped.agg(value="mean", n_observations="count").reset_index()
  return summary.rename(columns={boundary_column: "admin_boundary_id"})

def join_poverty_stats_to_geometry(stats: pd.DataFrame, boundaries: Any) -> Any:
  if not GEOPANDAS_AVAILABLE:
    raise RuntimeError("geopandas not installed - see module docstring; this is a scaffold stub.")
  raise NotImplementedError("join_poverty_stats_to_geometry is a scaffold stub; requires geopandas + boundary wiring before use.")
  
