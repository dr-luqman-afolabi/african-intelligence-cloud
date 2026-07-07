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


def _norm(value: Any) -> str:
    return str(value).strip().lower()


def merge_poverty_with_geojson(
    geojson: dict[str, Any],
    poverty_by_geo: list[dict[str, Any]],
    geojson_property_key: str,
) -> dict[str, Any]:
    """Merges computed poverty indices into a GeoJSON FeatureCollection's feature properties.

    Matches on `geojson_property_key` first, falling back to `admin_code`/`admin_name` (present
    on persisted boundaries from spatial_boundary_service). Returns only features that matched a
    row — geometries with no poverty data would render as blank/null on the map anyway — each
    carrying a `rank` field (by headcount, descending) so the frontend doesn't need to re-sort.
    """
    poverty_lookup = {_norm(row["geo_value"]): row for row in poverty_by_geo}

    def _feature_key(feature: dict[str, Any]) -> str | None:
        props = feature.get("properties", {})
        for key in (geojson_property_key, "admin_code", "admin_name"):
            if key in props and props[key] not in (None, ""):
                return _norm(props[key])
        return None

    matched_features = []
    for feature in geojson.get("features", []):
        key = _feature_key(feature)
        match = poverty_lookup.get(key) if key else None
        if not match:
            continue
        properties = dict(feature.get("properties", {}))
        properties.update({
            "poverty_headcount": match["headcount"],
            "poverty_gap": match["poverty_gap"],
            "squared_poverty_gap": match["squared_poverty_gap"],
            "gini": match["gini"],
            "n_obs": match["n_obs"],
            "geo_value": match["geo_value"],
        })
        matched_features.append({**feature, "properties": properties})

    matched_features.sort(key=lambda f: f["properties"]["poverty_headcount"], reverse=True)
    for idx, feature in enumerate(matched_features, start=1):
        feature["properties"]["rank"] = idx

    return {"type": "FeatureCollection", "features": matched_features}


def compute_morans_i_and_lisa(
    merged_geojson: dict[str, Any] | None,
) -> tuple[dict[str, Any], list[dict[str, Any]] | None]:
    """Computes Moran's I global autocorrelation and LISA local cluster classification.

    Takes the *merged* (matched + ranked) GeoJSON so geometry and poverty values are guaranteed
    to be in the same order — building the weights matrix from the raw input geojson while reading
    values from a separately-sorted poverty list (the previous approach) silently misaligned the
    two whenever they weren't already in identical order.
    """
    features = (merged_geojson or {}).get("features", [])
    if len(features) < 5:
        return {
            "available": False, "moran_i": None, "p_value": None,
            "note": "Moran's I / LISA require at least 5 matched geographic units.",
        }, None

    try:
        import geopandas as gpd
        from shapely.geometry import shape
        from libpysal.weights import Queen
        from esda.moran import Moran, Moran_Local

        geoms = [shape(f["geometry"]) for f in features]
        values = [f["properties"]["poverty_headcount"] for f in features]
        gdf = gpd.GeoDataFrame({"value": values}, geometry=geoms, crs="EPSG:4326")

        w = Queen.from_dataframe(gdf, use_index=False)
        w.transform = "r"

        moran = Moran(gdf["value"].to_numpy(), w)
        morans_i = {
            "available": True,
            "moran_i": float(moran.I),
            "p_value": float(moran.p_sim),
            "z_score": float(moran.z_sim),
            "method": "Queen contiguity weights, PySAL esda.Moran",
        }

        lisa = Moran_Local(gdf["value"].to_numpy(), w)
        quadrant_labels = {1: "HH", 2: "LH", 3: "LL", 4: "HL"}
        lisa_clusters = []
        for i, feature in enumerate(features):
            props = feature["properties"]
            significant = lisa.p_sim[i] < 0.05
            lisa_clusters.append({
                "admin_name": props.get("admin_name") or props.get("geo_value"),
                "admin_code": props.get("admin_code"),
                "cluster": quadrant_labels[lisa.q[i]] if significant else "Not Significant",
                "local_i": float(lisa.Is[i]),
                "p_value": float(lisa.p_sim[i]),
            })
        return morans_i, lisa_clusters
    except Exception as exc:
        logger.warning("Spatial statistics could not be computed: %s", exc)
        return {
            "available": False, "moran_i": None, "p_value": None,
            "note": f"Moran's I / LISA could not be computed: {exc}",
        }, None


def build_spatial_map_payload(
    poverty_by_geo: list[dict[str, Any]],
    merged_geojson: dict[str, Any] | None,
    morans_i: dict[str, Any],
    lisa_clusters: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    """Builds map-ready JSON for the frontend spatial poverty view."""
    return {
        "rankings": poverty_by_geo,
        "geojson": merged_geojson,
        "morans_i": morans_i,
        "lisa_clusters": lisa_clusters,
    }
