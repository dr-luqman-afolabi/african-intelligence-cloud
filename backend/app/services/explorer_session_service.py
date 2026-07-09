"""Interactive Spatial Explorer — session run engine.

Turns a saved :class:`MicrodataExplorerSession` into an aggregated,
choropleth-ready result by delegating to the same spatial analysis services
the one-shot ``/analyze/spatial-*`` endpoints use. Adds row-level filtering
(the explorer's FilterPanel) applied to the microdata *before* aggregation.

Security: only aggregated GeoJSON / summary tables are produced and stored —
raw respondent rows are never returned to the caller.
"""
from __future__ import annotations

import json
import logging
from typing import Any

import pandas as pd
from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.models.microdata import (
    ExplorerLayer,
    MicrodataAnalysisJob,
    MicrodataAnalysisResult,
    MicrodataDataset,
    MicrodataExplorerSession,
    MicrodataJobStatus,
    MicrodataJobType,
)
from app.services.agriculture_analysis_service import (
    compute_spatial_agriculture,
    generate_agriculture_interpretation,
)
from app.services.diversification_analysis_service import (
    compute_spatial_diversification,
    generate_diversification_interpretation,
)
from app.services.microdata_metadata_service import load_dataframe
from app.services.microdata_storage_service import download_microdata_bytes
from app.services.poverty_analysis_service import generate_interpretation
from app.services.spatial_analysis_service import (
    build_spatial_map_payload,
    compute_morans_i_and_lisa,
    compute_spatial_poverty,
    merge_poverty_with_geojson,
    merge_stats_with_geojson,
)
from app.services.spatial_boundary_service import get_boundaries_geojson
from app.services.variable_mapping_service import get_mappings_dict

logger = logging.getLogger(__name__)

_LAYER_TO_JOBTYPE = {
    ExplorerLayer.POVERTY: MicrodataJobType.SPATIAL_POVERTY,
    ExplorerLayer.AGRICULTURE: MicrodataJobType.SPATIAL_AGRICULTURE,
    ExplorerLayer.DIVERSIFICATION: MicrodataJobType.SPATIAL_DIVERSIFICATION,
}

# rank_field / Moran's value_field per layer, matching the /analyze/spatial-* endpoints
_LAYER_VALUE_FIELD = {
    ExplorerLayer.POVERTY: "poverty_headcount",
    ExplorerLayer.AGRICULTURE: "crop_yield",
    ExplorerLayer.DIVERSIFICATION: "crop_simpson_index",
}


def coerce_layer(value: Any) -> ExplorerLayer:
    if isinstance(value, ExplorerLayer):
        return value
    try:
        return ExplorerLayer(str(value).lower())
    except ValueError:
        raise HTTPException(status_code=422, detail=f"Unknown explorer layer '{value}'")


def apply_filters(df: pd.DataFrame, filters: list[dict] | None) -> pd.DataFrame:
    """Apply row-level filters to the microdata before aggregation.

    Each filter is ``{"variable": col, "op": one_of, "value": v}``. Unknown
    columns are ignored (so a stale saved filter never hard-fails a run).
    """
    if not filters:
        return df
    out = df
    for f in filters:
        col = f.get("variable")
        op = (f.get("op") or "eq").lower()
        val = f.get("value")
        if not col or col not in out.columns:
            continue
        series = out[col]
        try:
            if op == "eq":
                out = out[series == val]
            elif op == "ne":
                out = out[series != val]
            elif op == "in":
                out = out[series.isin(val if isinstance(val, (list, tuple)) else [val])]
            elif op == "not_in":
                out = out[~series.isin(val if isinstance(val, (list, tuple)) else [val])]
            elif op == "gt":
                out = out[pd.to_numeric(series, errors="coerce") > float(val)]
            elif op == "gte":
                out = out[pd.to_numeric(series, errors="coerce") >= float(val)]
            elif op == "lt":
                out = out[pd.to_numeric(series, errors="coerce") < float(val)]
            elif op == "lte":
                out = out[pd.to_numeric(series, errors="coerce") <= float(val)]
            elif op == "between" and isinstance(val, (list, tuple)) and len(val) == 2:
                num = pd.to_numeric(series, errors="coerce")
                out = out[(num >= float(val[0])) & (num <= float(val[1]))]
            elif op == "contains":
                out = out[series.astype(str).str.contains(str(val), case=False, na=False)]
        except (ValueError, TypeError) as exc:
            logger.warning("Skipping unappliable filter %s: %s", f, exc)
            continue
    return out


def _load_df(dataset: MicrodataDataset) -> pd.DataFrame:
    content = download_microdata_bytes(dataset.storage_path)
    df, _ = load_dataframe(content, dataset.file_type.value)
    return df


def _resolve_boundary(db: Session, session: MicrodataExplorerSession, state: dict) -> dict | None:
    raw = state.get("geojson_boundary_file")
    if raw:
        try:
            return json.loads(raw) if isinstance(raw, str) else raw
        except (json.JSONDecodeError, TypeError) as exc:
            logger.warning("Could not parse geojson_boundary_file: %s", exc)
    if session.country_iso3 and session.admin_level:
        try:
            return get_boundaries_geojson(db, session.country_iso3, session.admin_level)
        except HTTPException as exc:
            logger.warning(
                "No persisted boundaries for %s/%s: %s",
                session.country_iso3, session.admin_level, exc.detail,
            )
    return None


def run_session_layer(
    db: Session,
    session: MicrodataExplorerSession,
    current_user,
) -> dict:
    """Execute the session's active layer over its (filtered) dataset and
    persist a MicrodataAnalysisJob + MicrodataAnalysisResult. Returns an
    AnalysisResultResponse-shaped dict."""
    if session.dataset_id is None:
        raise HTTPException(status_code=400, detail="Session has no dataset loaded")

    dataset = db.query(MicrodataDataset).filter(MicrodataDataset.id == session.dataset_id).first()
    if not dataset:
        raise HTTPException(status_code=404, detail="Dataset not found")
    if dataset.uploaded_by != current_user.id:
        raise HTTPException(status_code=403, detail="You do not have access to this dataset")

    layer = coerce_layer(session.active_layer)
    state: dict = dict(session.state or {})
    geo_variable = state.get("geo_variable")
    if not geo_variable:
        raise HTTPException(status_code=400, detail="state.geo_variable is required to run a spatial layer")

    job = MicrodataAnalysisJob(
        dataset_id=dataset.id,
        job_type=_LAYER_TO_JOBTYPE[layer],
        status=MicrodataJobStatus.RUNNING,
        parameters={"explorer_session_id": str(session.id), "layer": layer.value, "state": state},
        requested_by=current_user.id,
    )
    db.add(job)
    db.commit()
    db.refresh(job)

    try:
        df = _load_df(dataset)
        df = apply_filters(df, state.get("filters"))
        if geo_variable not in df.columns:
            raise ValueError(f"Geography variable '{geo_variable}' not found in dataset")

        weight = state.get("weight_variable")
        geojson_data = _resolve_boundary(db, session, state)
        value_field = _LAYER_VALUE_FIELD[layer]

        if layer == ExplorerLayer.POVERTY:
            welfare = state.get("welfare_variable")
            poverty_line = state.get("poverty_line")
            if not welfare or poverty_line is None:
                raise ValueError("Poverty layer requires state.welfare_variable and state.poverty_line")
            if welfare not in df.columns:
                raise ValueError(f"Welfare variable '{welfare}' not found in dataset")
            stats_by_geo = compute_spatial_poverty(df, geo_variable, welfare, float(poverty_line), weight)
            merged = merge_poverty_with_geojson(geojson_data, stats_by_geo, geo_variable) if geojson_data else None
            interpretation = generate_interpretation(
                stats_by_geo[0] if stats_by_geo else {"headcount": 0.0, "poverty_gap": 0.0, "squared_poverty_gap": 0.0, "gini": 0.0, "n_obs": 0},
                {geo_variable: stats_by_geo},
            )

        elif layer == ExplorerLayer.AGRICULTURE:
            mapping = get_mappings_dict(db, dataset.id)
            mapping.update(state.get("variable_overrides") or {})
            if not mapping:
                raise ValueError("Agriculture layer requires a saved variable mapping (POST /microdata/mapping).")
            stats_by_geo = compute_spatial_agriculture(df, mapping, geo_variable, weight)
            merged = (
                merge_stats_with_geojson(geojson_data, stats_by_geo, geo_variable, rank_field=value_field)
                if geojson_data else None
            )
            interpretation = generate_agriculture_interpretation(
                stats_by_geo[0] if stats_by_geo else {"n_obs": 0}, {geo_variable: stats_by_geo}
            )

        else:  # DIVERSIFICATION
            crop = state.get("crop_columns")
            income = state.get("income_columns")
            livelihood = state.get("livelihood_columns")
            livestock = state.get("livestock_columns")
            if not any([crop, income, livelihood, livestock]):
                raise ValueError(
                    "Diversification layer requires at least one of crop_columns, income_columns, "
                    "livelihood_columns, livestock_columns in state."
                )
            stats_by_geo = compute_spatial_diversification(
                df, geo_variable, crop, income, livelihood, livestock, weight
            )
            merged = (
                merge_stats_with_geojson(geojson_data, stats_by_geo, geo_variable, rank_field=value_field)
                if geojson_data else None
            )
            interpretation = generate_diversification_interpretation(
                stats_by_geo[0] if stats_by_geo else {"n_obs": 0}, {geo_variable: stats_by_geo}
            )

        morans_i, lisa_clusters = compute_morans_i_and_lisa(merged, value_field=value_field)
        map_payload = build_spatial_map_payload(stats_by_geo, merged, morans_i, lisa_clusters)

        result = MicrodataAnalysisResult(
            job_id=job.id,
            summary_stats={"top_geo": stats_by_geo[0] if stats_by_geo else None,
                           "n_units": len(stats_by_geo), "value_field": value_field},
            tables={"by_geography": stats_by_geo},
            charts=map_payload,
            geojson=merged,
            interpretation_text=interpretation,
        )
        db.add(result)
        job.status = MicrodataJobStatus.COMPLETED

        # keep the session in sync for replay
        last_job_ids = dict((session.state or {}).get("last_job_ids", {}))
        last_job_ids[layer.value] = str(job.id)
        new_state = dict(session.state or {})
        new_state["last_job_ids"] = last_job_ids
        session.state = new_state
        session.last_result_job_id = job.id
        db.add(session)
        db.commit()
        db.refresh(result)

        return {
            "job_id": job.id,
            "status": job.status,
            "job_type": job.job_type,
            "summary_stats": result.summary_stats,
            "tables": result.tables,
            "charts": map_payload,
            "geojson": merged,
            "interpretation_text": interpretation,
        }
    except HTTPException:
        job.status = MicrodataJobStatus.FAILED
        db.commit()
        raise
    except Exception as exc:
        logger.error("Explorer session run failed", exc_info=True)
        job.status = MicrodataJobStatus.FAILED
        job.error_message = str(exc)
        db.commit()
        raise HTTPException(status_code=422, detail=f"Explorer run failed: {exc}")
