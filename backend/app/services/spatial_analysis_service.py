from __future__ import annotations

import logging
from typing import Any

import pandas as pd

from app.services.poverty_analysis_service import compute_fgt_indices

logger = logging.getLogger(__name__)


def compute_spatial_poverty(
    df: pd.DataFrame,
    geo_variable: str,
    welfare_variable: str,
    poverty_line: float,
    weight_variable: str | None = None,
) -> list[dict[str, Any]]:
    """Computes poverty indices for each geographic unit (e.g. district or province)."""
    results = []
    for geo_value, geo_df in df.groupby(geo_variable, dropna=True):
        stats = compute_fgt_indices(geo_df, welfare_variable, poverty_line, weight_variable)
        stats["geo_value"] = str(geo_value)
        results.append(stats)
    return sorted(results, key=lambda r: r["headcount"], reverse=True)


def merge_poverty_with_geojson(
    geojson: dict[str, Any],
    poverty_by_geo: list[dict[str, Any]],
    geojson_property_key: str,
) -> dict[str, Any]:
    """Merges computed poverty indices into a GeoJSON FeatureCollection's feature properties,
    matching on `geojson_property_key` against each row's `geo_value`.
    """
    poverty_lookup = {row["geo_value"]: row for row in poverty_by_geo}

    merged_features = []
    for feature in geojson.get("features", []):
        properties = dict(feature.get("properties", {}))
        key_value = str(properties.get(geojson_property_key, ""))
        match = poverty_lookup.get(key_value)
        if match:
            properties["poverty_headcount"] = match["headcount"]
            properties["poverty_gap"] = match["poverty_gap"]
            properties["squared_poverty_gap"] = match["squared_poverty_gap"]
            properties["gini"] = match["gini"]
            properties["n_obs"] = match["n_obs"]
        else:
            properties["poverty_headcount"] = None
        merged_features.append({**feature, "properties": properties})

    return {**geojson, "features": merged_features}


def compute_morans_i(poverty_by_geo: list[dict[str, Any]], geojson: dict[str, Any] | None = None) -> dict[str, Any]:
    """Attempts to compute Moran's I spatial autocorrelation statistic for poverty headcount rates
    across geographic units, using PySAL if available. Falls back to a placeholder result when
    PySAL/geopandas are not installed or a spatial weights matrix cannot be built from the input.
    """
    try:
        import geopandas as gpd
        from libpysal.weights import Queen
        from esda.moran import Moran

        if not geojson:
            raise ValueError("geojson_boundary_file is required to compute Moran's I")

        gdf = gpd.GeoDataFrame.from_features(geojson.get("features", []))
        headcounts = [row["headcount"] for row in poverty_by_geo]

        if len(gdf) != len(poverty_by_geo) or len(gdf) < 3:
            raise ValueError("Insufficient matching geographic units to compute spatial weights")

        w = Queen.from_dataframe(gdf, use_index=False)
        w.transform = "r"
        moran = Moran(headcounts, w)
        return {
            "available": True,
            "moran_i": float(moran.I),
            "p_value": float(moran.p_sim),
            "method": "Queen contiguity weights, PySAL esda.Moran",
        }
    except Exception as exc:
        logger.info("Moran's I not computed (placeholder returned): %s", exc)
        return {
            "available": False,
            "moran_i": None,
            "p_value": None,
            "note": (
                "Moran's I requires PySAL (libpysal/esda) and a valid GeoJSON boundary file "
                "with one polygon per geographic unit. Install these packages and supply "
                "geojson_boundary_file to enable this statistic."
            ),
        }


def build_spatial_map_payload(
    poverty_by_geo: list[dict[str, Any]],
    merged_geojson: dict[str, Any] | None,
    morans_i: dict[str, Any],
) -> dict[str, Any]:
    """Builds map-ready JSON for the frontend spatial poverty view."""
    return {
        "rankings": poverty_by_geo,
        "geojson": merged_geojson,
        "morans_i": morans_i,
    }
