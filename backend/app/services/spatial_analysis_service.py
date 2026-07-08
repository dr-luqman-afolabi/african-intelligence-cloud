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
    Thin wrapper over merge_stats_with_geojson() for the poverty-specific field set."""
    return merge_stats_with_geojson(
        geojson, poverty_by_geo, geojson_property_key,
        rank_field="poverty_headcount",
        field_map={
            "headcount": "poverty_headcount",
            "poverty_gap": "poverty_gap",
            "squared_poverty_gap": "squared_poverty_gap",
            "gini": "gini",
            "n_obs": "n_obs",
        },
    )


def merge_stats_with_geojson(
    geojson: dict[str, Any],
    stats_by_geo: list[dict[str, Any]],
    geojson_property_key: str,
    rank_field: str,
    field_map: dict[str, str] | None = None,
) -> dict[str, Any]:
    """Merges any per-geography stats (poverty, agriculture, or
    diversification) into a GeoJSON FeatureCollection's feature properties —
    the general form merge_poverty_with_geojson() delegates to.

    Matches on `geojson_property_key` first, falling back to `admin_code`/`admin_name` (present
    on persisted boundaries from spatial_boundary_service). Returns only features that matched a
    row — geometries with no data would render as blank/null on the map anyway — each carrying a
    `rank` field (by `rank_field`, descending) so the frontend doesn't need to re-sort.

    `field_map` renames stat dict keys -> GeoJSON property names (e.g.
    {"headcount": "poverty_headcount"}); defaults to keeping stat keys as-is.
    """
    lookup = {_norm(row["geo_value"]): row for row in stats_by_geo}

    def _feature_key(feature: dict[str, Any]) -> str | None:
        props = feature.get("properties", {})
        for key in (geojson_property_key, "admin_code", "admin_name"):
            if key in props and props[key] not in (None, ""):
                return _norm(props[key])
        return None

    matched_features = []
    for feature in geojson.get("features", []):
        key = _feature_key(feature)
        match = lookup.get(key) if key else None
        if not match:
            continue
        properties = dict(feature.get("properties", {}))
        for stat_key, value in match.items():
            if stat_key == "geo_value":
                continue
            out_key = (field_map or {}).get(stat_key, stat_key)
            properties[out_key] = value
        properties["geo_value"] = match["geo_value"]
        matched_features.append({**feature, "properties": properties})

    matched_features = [f for f in matched_features if f["properties"].get(rank_field) is not None]
    matched_features.sort(key=lambda f: f["properties"][rank_field], reverse=True)
    for idx, feature in enumerate(matched_features, start=1):
        feature["properties"]["rank"] = idx

    return {"type": "FeatureCollection", "features": matched_features}


def compute_morans_i_and_lisa(
    merged_geojson: dict[str, Any] | None,
    value_field: str = "poverty_headcount",
) -> tuple[dict[str, Any], list[dict[str, Any]] | None]:
    """Computes Moran's I global autocorrelation and LISA local cluster classification
    over `value_field` (any numeric property merged onto the GeoJSON — poverty headcount,
    crop yield, a diversification index, ...). LISA's HH/LL quadrants are the hotspot/
    coldspot classification: HH = statistically significant cluster of high values
    surrounded by high neighbors (a hotspot), LL = the low-value equivalent (a coldspot).

    Takes the *merged* (matched + ranked) GeoJSON so geometry and values are guaranteed
    to be in the same order — building the weights matrix from the raw input geojson while
    reading values from a separately-sorted stats list would silently misalign the two
    whenever they weren't already in identical order.
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
        values = [f["properties"][value_field] for f in features]
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
