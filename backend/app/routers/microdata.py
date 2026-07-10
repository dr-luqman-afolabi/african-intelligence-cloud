from __future__ import annotations

import json
import logging
from uuid import UUID

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.microdata import (
    MicrodataAccessStatus,
    MicrodataAnalysisJob,
    MicrodataAnalysisResult,
    MicrodataDataset,
    MicrodataFileType,
    MicrodataJobStatus,
    MicrodataJobType,
    MicrodataVariable,
)
from app.schemas.microdata import (
    AgricultureAnalysisRequest,
    AIInterpretRequest,
    AnalysisResultResponse,
    DiversificationAnalysisRequest,
    MicrodataDatasetListResponse,
    MicrodataDatasetResponse,
    MicrodataVariableResponse,
    PovertyAnalysisRequest,
    SaveVariableMappingRequest,
    SpatialAgricultureAnalysisRequest,
    SpatialDiversificationAnalysisRequest,
    SpatialPovertyAnalysisRequest,
    VariableMappingResponse,
    VariableMappingSuggestResponse,
)
from app.services.agriculture_analysis_service import (
    build_agriculture_charts_payload,
    compute_agriculture_stats,
    compute_grouped_agriculture,
    compute_spatial_agriculture,
    generate_agriculture_interpretation,
)
from app.services.auth_service import get_current_user
from app.services.diversification_analysis_service import (
    build_diversification_charts_payload,
    compute_diversification_stats,
    compute_grouped_diversification,
    compute_spatial_diversification,
    generate_diversification_interpretation,
)
from app.services.microdata_metadata_service import (
    extract_metadata,
    extract_supported_file_from_zip,
    load_dataframe,
)
from app.services.microdata_storage_service import (
    download_microdata_bytes,
    upload_microdata_file,
    validate_microdata_file,
)
from app.services.poverty_analysis_service import (
    build_charts_payload,
    compute_fgt_indices,
    compute_grouped_poverty,
    generate_interpretation,
)
from app.services.spatial_analysis_service import (
    build_spatial_map_payload,
    compute_morans_i_and_lisa,
    compute_spatial_poverty,
    merge_poverty_with_geojson,
    merge_stats_with_geojson,
)
from app.services.spatial_boundary_service import get_boundaries_geojson
from app.services.boundary_provider_service import fetch_admin_boundaries
from app.services.variable_mapping_service import get_mappings_dict, save_mappings, suggest_mappings

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/microdata", tags=["Microdata"])
security = HTTPBearer()


def _get_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db),
):
    return get_current_user(db, credentials.credentials)


def _get_owned_dataset(db: Session, dataset_id: UUID, current_user) -> MicrodataDataset:
    dataset = db.query(MicrodataDataset).filter(MicrodataDataset.id == dataset_id).first()
    if not dataset:
        raise HTTPException(status_code=404, detail="Dataset not found")
    # Shared catalog: any authenticated user may read/analyze stored datasets.
    return dataset


def _load_dataset_dataframe(dataset: MicrodataDataset):
    content = download_microdata_bytes(dataset.storage_path)
    df, _ = load_dataframe(content, dataset.file_type.value)
    return df


@router.post("/upload", response_model=MicrodataDatasetResponse, status_code=201)
async def upload_microdata(
    file: UploadFile = File(...),
    name: str = Form(...),
    country_iso3: str | None = Form(None),
    project_id: str | None = Form(None),
    db: Session = Depends(get_db),
    current_user=Depends(_get_user),
):
    """Uploads a raw microdata file (.csv, .xlsx, .dta, .sav, or a .zip
    containing one of those), stores it privately in Cloud Storage, and
    extracts variable-level metadata. Raw microdata is never made public;
    only aggregated analysis results are ever returned via the analyze
    endpoints.
    """
    try:
        ext = validate_microdata_file(file)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))

    content = await file.read()
    original_filename = file.filename or name

    if ext == "zip":
        try:
            content, ext, inner_filename = extract_supported_file_from_zip(content)
            original_filename = inner_filename
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc))

    try:
        metadata = extract_metadata(content, ext, original_filename)
    except Exception as exc:
        logger.error("Metadata extraction failed", exc_info=True)
        raise HTTPException(status_code=422, detail=f"Could not parse microdata file: {exc}")

    country_guess = country_iso3 or metadata.get("detected_country")
    survey_guess = metadata.get("detected_series")
    year_guess = metadata.get("detected_year")
    storage_path, size_bytes = await upload_microdata_file(
        content, original_filename, country_guess, survey_guess, year_guess
    )

    dataset = MicrodataDataset(
        project_id=UUID(project_id) if project_id else None,
        name=name,
        original_filename=original_filename,
        file_type=MicrodataFileType(ext),
        storage_path=storage_path,
        file_size_bytes=size_bytes,
        country_iso3=country_guess,
        survey_series=survey_guess,
        year=year_guess,
        row_count=metadata["row_count"],
        column_count=metadata["column_count"],
        missing_cells=metadata["missing_cells"],
        access_status=MicrodataAccessStatus.USER_UPLOAD,
        uploaded_by=current_user.id,
    )
    db.add(dataset)
    db.flush()

    for var in metadata["variables"]:
        db.add(MicrodataVariable(
            dataset_id=dataset.id,
            variable_name=var["variable_name"],
            variable_label=var["variable_label"],
            value_labels=var["value_labels"],
            variable_index=var["variable_index"],
            inferred_dtype=var["inferred_dtype"],
            missing_count=var["missing_count"],
        ))

    db.commit()
    db.refresh(dataset)
    return dataset


@router.get("/datasets", response_model=MicrodataDatasetListResponse)
def list_microdata_datasets(
    skip: int = 0,
    limit: int = 50,
    db: Session = Depends(get_db),
    current_user=Depends(_get_user),
):
    # Shared catalog: show all uploaded/cleaned/stored datasets to every authenticated user
    query = db.query(MicrodataDataset)
    total = query.count()
    items = query.order_by(MicrodataDataset.created_at.desc()).offset(skip).limit(limit).all()
    return {"items": items, "total": total}


@router.get("/datasets/{dataset_id}", response_model=MicrodataDatasetResponse)
def get_microdata_dataset(
    dataset_id: UUID,
    db: Session = Depends(get_db),
    current_user=Depends(_get_user),
):
    return _get_owned_dataset(db, dataset_id, current_user)


@router.get("/datasets/{dataset_id}/variables", response_model=list[MicrodataVariableResponse])
def list_microdata_variables(
    dataset_id: UUID,
    db: Session = Depends(get_db),
    current_user=Depends(_get_user),
):
    dataset = _get_owned_dataset(db, dataset_id, current_user)
    return (
        db.query(MicrodataVariable)
        .filter(MicrodataVariable.dataset_id == dataset.id)
        .order_by(MicrodataVariable.variable_index)
        .all()
    )


@router.get("/datasets/{dataset_id}/mapping/suggest", response_model=VariableMappingSuggestResponse)
def suggest_variable_mapping(
    dataset_id: UUID,
    db: Session = Depends(get_db),
    current_user=Depends(_get_user),
):
    """Auto-detect likely standard-concept mappings (household_id, welfare,
    gender, district, ...) from this dataset's variable names/labels. Purely
    suggestions — nothing is saved until POST /microdata/mapping is called."""
    dataset = _get_owned_dataset(db, dataset_id, current_user)
    variables = (
        db.query(MicrodataVariable)
        .filter(MicrodataVariable.dataset_id == dataset.id)
        .order_by(MicrodataVariable.variable_index)
        .all()
    )
    var_dicts = [{"variable_name": v.variable_name, "variable_label": v.variable_label} for v in variables]
    return {"dataset_id": dataset.id, "suggestions": suggest_mappings(var_dicts)}


@router.get("/datasets/{dataset_id}/mapping", response_model=list[VariableMappingResponse])
def get_variable_mapping(
    dataset_id: UUID,
    db: Session = Depends(get_db),
    current_user=Depends(_get_user),
):
    """List the currently confirmed standard-concept mappings for a dataset."""
    dataset = _get_owned_dataset(db, dataset_id, current_user)
    from app.models.microdata import VariableMapping
    return db.query(VariableMapping).filter(VariableMapping.dataset_id == dataset.id).all()


@router.post("/mapping", response_model=list[VariableMappingResponse])
def save_variable_mapping(
    payload: SaveVariableMappingRequest,
    db: Session = Depends(get_db),
    current_user=Depends(_get_user),
):
    """Save confirmed standard-concept -> raw-variable mappings for a dataset.
    The poverty/agriculture/diversification engines resolve concepts (e.g.
    "welfare", "gender") through these mappings rather than requiring callers
    to know each survey's own raw column names."""
    dataset = _get_owned_dataset(db, payload.dataset_id, current_user)
    mappings = [m.model_dump() for m in payload.mappings]
    return save_mappings(db, dataset.id, mappings, user_id=current_user.id, auto_detected=False)


@router.post("/analyze/poverty", response_model=AnalysisResultResponse)
def analyze_poverty(
    payload: PovertyAnalysisRequest,
    db: Session = Depends(get_db),
    current_user=Depends(_get_user),
):
    """Runs poverty headcount, gap, squared gap, Gini and grouped poverty analysis on a dataset.
    Only aggregated statistics are returned; raw microdata rows are never exposed.
    """
    dataset = _get_owned_dataset(db, payload.dataset_id, current_user)

    job = MicrodataAnalysisJob(
        dataset_id=dataset.id,
        job_type=MicrodataJobType.POVERTY,
        status=MicrodataJobStatus.RUNNING,
        parameters=payload.model_dump(mode="json"),
        requested_by=current_user.id,
    )
    db.add(job)
    db.commit()
    db.refresh(job)

    try:
        df = _load_dataset_dataframe(dataset)

        if payload.welfare_variable not in df.columns:
            raise ValueError(f"Welfare variable '{payload.welfare_variable}' not found in dataset")

        overall = compute_fgt_indices(df, payload.welfare_variable, payload.poverty_line, payload.weight_variable)

        grouped_results: dict[str, list[dict]] = {}
        tables: dict[str, object] = {"overall": overall}
        group_by_vars = list(payload.group_by or [])
        if payload.geography_variable and payload.geography_variable not in group_by_vars:
            group_by_vars.append(payload.geography_variable)

        for group_var in group_by_vars:
            if group_var in df.columns:
                rows = compute_grouped_poverty(
                    df, payload.welfare_variable, payload.poverty_line, group_var, payload.weight_variable
                )
                grouped_results[group_var] = rows
                tables[group_var] = rows

        charts = build_charts_payload(overall, grouped_results)
        interpretation = generate_interpretation(overall, grouped_results)

        result = MicrodataAnalysisResult(
            job_id=job.id,
            summary_stats=overall,
            tables=tables,
            charts=charts,
            interpretation_text=interpretation,
        )
        db.add(result)
        job.status = MicrodataJobStatus.COMPLETED
        db.commit()
        db.refresh(result)

        return {
            "job_id": job.id,
            "status": job.status,
            "job_type": job.job_type,
            "summary_stats": overall,
            "tables": tables,
            "charts": charts,
            "interpretation_text": interpretation,
        }
    except Exception as exc:
        logger.error("Poverty analysis failed", exc_info=True)
        job.status = MicrodataJobStatus.FAILED
        job.error_message = str(exc)
        db.commit()
        raise HTTPException(status_code=422, detail=f"Poverty analysis failed: {exc}")


@router.post("/analyze/spatial-poverty", response_model=AnalysisResultResponse)
def analyze_spatial_poverty(
    payload: SpatialPovertyAnalysisRequest,
    db: Session = Depends(get_db),
    current_user=Depends(_get_user),
):
    """Computes district/province-level poverty and merges results into a GeoJSON boundary file
    for map rendering, with a Moran's I placeholder when PySAL is unavailable.
    """
    dataset = _get_owned_dataset(db, payload.dataset_id, current_user)

    job = MicrodataAnalysisJob(
        dataset_id=dataset.id,
        job_type=MicrodataJobType.SPATIAL_POVERTY,
        status=MicrodataJobStatus.RUNNING,
        parameters=payload.model_dump(mode="json"),
        requested_by=current_user.id,
    )
    db.add(job)
    db.commit()
    db.refresh(job)

    try:
        df = _load_dataset_dataframe(dataset)

        if payload.welfare_variable not in df.columns:
            raise ValueError(f"Welfare variable '{payload.welfare_variable}' not found in dataset")
        if payload.geo_variable not in df.columns:
            raise ValueError(f"Geography variable '{payload.geo_variable}' not found in dataset")

        poverty_by_geo = compute_spatial_poverty(
            df, payload.geo_variable, payload.welfare_variable, payload.poverty_line, payload.weight_variable
        )

        geojson_data = _resolve_boundary_geojson(db, payload, dataset)

        merged_geojson = (
            merge_poverty_with_geojson(geojson_data, poverty_by_geo, payload.geo_variable) if geojson_data else None
        )
        morans_i, lisa_clusters = compute_morans_i_and_lisa(merged_geojson)
        map_payload = build_spatial_map_payload(poverty_by_geo, merged_geojson, morans_i, lisa_clusters)

        fallback_stats = {
            "headcount": 0.0, "poverty_gap": 0.0, "squared_poverty_gap": 0.0, "gini": 0.0, "n_obs": 0,
        }
        interpretation = generate_interpretation(
            poverty_by_geo[0] if poverty_by_geo else fallback_stats,
            {payload.geo_variable: poverty_by_geo},
        )

        result = MicrodataAnalysisResult(
            job_id=job.id,
            summary_stats={"top_poverty_geo": poverty_by_geo[0] if poverty_by_geo else None},
            tables={"by_geography": poverty_by_geo},
            charts=map_payload,
            geojson=merged_geojson,
            interpretation_text=interpretation,
        )
        db.add(result)
        job.status = MicrodataJobStatus.COMPLETED
        db.commit()
        db.refresh(result)

        return {
            "job_id": job.id,
            "status": job.status,
            "job_type": job.job_type,
            "summary_stats": result.summary_stats,
            "tables": result.tables,
            "charts": map_payload,
            "geojson": merged_geojson,
            "interpretation_text": interpretation,
        }
    except Exception as exc:
        logger.error("Spatial poverty analysis failed", exc_info=True)
        job.status = MicrodataJobStatus.FAILED
        job.error_message = str(exc)
        db.commit()
        raise HTTPException(status_code=422, detail=f"Spatial poverty analysis failed: {exc}")


@router.post("/analyze/agriculture", response_model=AnalysisResultResponse)
def analyze_agriculture(
    payload: AgricultureAnalysisRequest,
    db: Session = Depends(get_db),
    current_user=Depends(_get_user),
):
    """Runs farm productivity and input-adoption analysis (crop yield, land/
    labour productivity, fertilizer/seed/irrigation/extension adoption,
    market participation, crop/livestock income). Resolves land_area,
    crop_output, crop_value, livestock, fertilizer, improved_seed,
    irrigation, extension and household_size through this dataset's saved
    VariableMapping, overridable per-request via variable_overrides."""
    dataset = _get_owned_dataset(db, payload.dataset_id, current_user)

    job = MicrodataAnalysisJob(
        dataset_id=dataset.id,
        job_type=MicrodataJobType.AGRICULTURE,
        status=MicrodataJobStatus.RUNNING,
        parameters=payload.model_dump(mode="json"),
        requested_by=current_user.id,
    )
    db.add(job)
    db.commit()
    db.refresh(job)

    try:
        df = _load_dataset_dataframe(dataset)
        mapping = get_mappings_dict(db, dataset.id)
        mapping.update(payload.variable_overrides or {})
        if not mapping:
            raise ValueError(
                "No variable mapping found for this dataset. Save a mapping via "
                "POST /microdata/mapping (or GET .../mapping/suggest for auto-detected candidates) first."
            )

        overall = compute_agriculture_stats(df, mapping, payload.weight_variable)

        grouped_results: dict[str, list[dict]] = {}
        tables: dict[str, object] = {"overall": overall}
        group_by_vars = list(payload.group_by or [])
        if payload.geography_variable and payload.geography_variable not in group_by_vars:
            group_by_vars.append(payload.geography_variable)

        for group_var in group_by_vars:
            if group_var in df.columns:
                rows = compute_grouped_agriculture(df, mapping, group_var, payload.weight_variable)
                grouped_results[group_var] = rows
                tables[group_var] = rows

        charts = build_agriculture_charts_payload(overall, grouped_results)
        interpretation = generate_agriculture_interpretation(overall, grouped_results)

        result = MicrodataAnalysisResult(
            job_id=job.id,
            summary_stats=overall,
            tables=tables,
            charts=charts,
            interpretation_text=interpretation,
        )
        db.add(result)
        job.status = MicrodataJobStatus.COMPLETED
        db.commit()
        db.refresh(result)

        return {
            "job_id": job.id,
            "status": job.status,
            "job_type": job.job_type,
            "summary_stats": overall,
            "tables": tables,
            "charts": charts,
            "interpretation_text": interpretation,
        }
    except Exception as exc:
        logger.error("Agriculture analysis failed", exc_info=True)
        job.status = MicrodataJobStatus.FAILED
        job.error_message = str(exc)
        db.commit()
        raise HTTPException(status_code=422, detail=f"Agriculture analysis failed: {exc}")


@router.post("/analyze/diversification", response_model=AnalysisResultResponse)
def analyze_diversification(
    payload: DiversificationAnalysisRequest,
    db: Session = Depends(get_db),
    current_user=Depends(_get_user),
):
    """Runs crop/income/livelihood/livestock diversification analysis
    (Simpson, Shannon, Herfindahl indices). Each *_columns list names the
    dataset's own per-crop/per-source value columns directly (e.g.
    ["maize_value", "beans_value", "cassava_value"]) — diversification is
    computed over the shares those columns represent per household."""
    dataset = _get_owned_dataset(db, payload.dataset_id, current_user)

    job = MicrodataAnalysisJob(
        dataset_id=dataset.id,
        job_type=MicrodataJobType.DIVERSIFICATION,
        status=MicrodataJobStatus.RUNNING,
        parameters=payload.model_dump(mode="json"),
        requested_by=current_user.id,
    )
    db.add(job)
    db.commit()
    db.refresh(job)

    try:
        df = _load_dataset_dataframe(dataset)
        if not any([payload.crop_columns, payload.income_columns, payload.livelihood_columns, payload.livestock_columns]):
            raise ValueError(
                "Provide at least one of crop_columns, income_columns, livelihood_columns, or livestock_columns."
            )

        overall = compute_diversification_stats(
            df,
            payload.crop_columns,
            payload.income_columns,
            payload.livelihood_columns,
            payload.livestock_columns,
            payload.weight_variable,
        )

        grouped_results: dict[str, list[dict]] = {}
        tables: dict[str, object] = {"overall": overall}
        for group_var in payload.group_by or []:
            if group_var in df.columns:
                rows = compute_grouped_diversification(
                    df, group_var, payload.crop_columns, payload.income_columns,
                    payload.livelihood_columns, payload.livestock_columns, payload.weight_variable,
                )
                grouped_results[group_var] = rows
                tables[group_var] = rows

        charts = build_diversification_charts_payload(overall, grouped_results)
        interpretation = generate_diversification_interpretation(overall, grouped_results)

        result = MicrodataAnalysisResult(
            job_id=job.id,
            summary_stats=overall,
            tables=tables,
            charts=charts,
            interpretation_text=interpretation,
        )
        db.add(result)
        job.status = MicrodataJobStatus.COMPLETED
        db.commit()
        db.refresh(result)

        return {
            "job_id": job.id,
            "status": job.status,
            "job_type": job.job_type,
            "summary_stats": overall,
            "tables": tables,
            "charts": charts,
            "interpretation_text": interpretation,
        }
    except Exception as exc:
        logger.error("Diversification analysis failed", exc_info=True)
        job.status = MicrodataJobStatus.FAILED
        job.error_message = str(exc)
        db.commit()
        raise HTTPException(status_code=422, detail=f"Diversification analysis failed: {exc}")


def _resolve_boundary_geojson(db, payload, dataset=None) -> dict | None:
    """Resolve boundary GeoJSON for a spatial analysis, in order of preference:
    inline file -> user-uploaded boundaries -> automatic openly-licensed
    boundaries (geoBoundaries). The last step means the choropleth renders on
    its own; iso3 comes from the request or, failing that, the dataset."""
    if payload.geojson_boundary_file:
        try:
            return json.loads(payload.geojson_boundary_file)
        except (json.JSONDecodeError, TypeError) as exc:
            logger.warning("Could not parse geojson_boundary_file: %s", exc)
    if payload.country_iso3 and payload.admin_level:
        try:
            geo = get_boundaries_geojson(db, payload.country_iso3, payload.admin_level)
            if geo and geo.get("features"):
                return geo
        except HTTPException as exc:
            logger.warning("No persisted boundaries for %s/%s: %s", payload.country_iso3, payload.admin_level, exc.detail)
    iso3 = payload.country_iso3 or (dataset.country_iso3 if dataset is not None else None)
    return fetch_admin_boundaries(iso3, getattr(payload, "admin_level", None))


@router.post("/analyze/spatial-agriculture", response_model=AnalysisResultResponse)
def analyze_spatial_agriculture(
    payload: SpatialAgricultureAnalysisRequest,
    db: Session = Depends(get_db),
    current_user=Depends(_get_user),
):
    """Agricultural productivity by admin unit, merged into choropleth-ready
    GeoJSON, with Moran's I / LISA hotspot detection over crop yield."""
    dataset = _get_owned_dataset(db, payload.dataset_id, current_user)

    job = MicrodataAnalysisJob(
        dataset_id=dataset.id,
        job_type=MicrodataJobType.SPATIAL_AGRICULTURE,
        status=MicrodataJobStatus.RUNNING,
        parameters=payload.model_dump(mode="json"),
        requested_by=current_user.id,
    )
    db.add(job)
    db.commit()
    db.refresh(job)

    try:
        df = _load_dataset_dataframe(dataset)
        if payload.geo_variable not in df.columns:
            raise ValueError(f"Geography variable '{payload.geo_variable}' not found in dataset")

        mapping = get_mappings_dict(db, dataset.id)
        mapping.update(payload.variable_overrides or {})
        if not mapping:
            raise ValueError("No variable mapping found for this dataset. Save a mapping via POST /microdata/mapping first.")

        stats_by_geo = compute_spatial_agriculture(df, mapping, payload.geo_variable, payload.weight_variable)

        geojson_data = _resolve_boundary_geojson(db, payload, dataset)
        merged_geojson = (
            merge_stats_with_geojson(geojson_data, stats_by_geo, payload.geo_variable, rank_field="crop_yield")
            if geojson_data else None
        )
        morans_i, lisa_clusters = compute_morans_i_and_lisa(merged_geojson, value_field="crop_yield")
        map_payload = build_spatial_map_payload(stats_by_geo, merged_geojson, morans_i, lisa_clusters)
        interpretation = generate_agriculture_interpretation(
            stats_by_geo[0] if stats_by_geo else {"n_obs": 0}, {payload.geo_variable: stats_by_geo}
        )

        result = MicrodataAnalysisResult(
            job_id=job.id,
            summary_stats={"top_geo": stats_by_geo[0] if stats_by_geo else None},
            tables={"by_geography": stats_by_geo},
            charts=map_payload,
            geojson=merged_geojson,
            interpretation_text=interpretation,
        )
        db.add(result)
        job.status = MicrodataJobStatus.COMPLETED
        db.commit()
        db.refresh(result)

        return {
            "job_id": job.id, "status": job.status, "job_type": job.job_type,
            "summary_stats": result.summary_stats, "tables": result.tables,
            "charts": map_payload, "geojson": merged_geojson, "interpretation_text": interpretation,
        }
    except Exception as exc:
        logger.error("Spatial agriculture analysis failed", exc_info=True)
        job.status = MicrodataJobStatus.FAILED
        job.error_message = str(exc)
        db.commit()
        raise HTTPException(status_code=422, detail=f"Spatial agriculture analysis failed: {exc}")


@router.post("/analyze/spatial-diversification", response_model=AnalysisResultResponse)
def analyze_spatial_diversification(
    payload: SpatialDiversificationAnalysisRequest,
    db: Session = Depends(get_db),
    current_user=Depends(_get_user),
):
    """Diversification indices by admin unit, merged into choropleth-ready
    GeoJSON, with Moran's I / LISA hotspot detection over the crop Simpson index."""
    dataset = _get_owned_dataset(db, payload.dataset_id, current_user)

    job = MicrodataAnalysisJob(
        dataset_id=dataset.id,
        job_type=MicrodataJobType.SPATIAL_DIVERSIFICATION,
        status=MicrodataJobStatus.RUNNING,
        parameters=payload.model_dump(mode="json"),
        requested_by=current_user.id,
    )
    db.add(job)
    db.commit()
    db.refresh(job)

    try:
        df = _load_dataset_dataframe(dataset)
        if payload.geo_variable not in df.columns:
            raise ValueError(f"Geography variable '{payload.geo_variable}' not found in dataset")
        if not any([payload.crop_columns, payload.income_columns, payload.livelihood_columns, payload.livestock_columns]):
            raise ValueError(
                "Provide at least one of crop_columns, income_columns, livelihood_columns, or livestock_columns."
            )

        stats_by_geo = compute_spatial_diversification(
            df, payload.geo_variable, payload.crop_columns, payload.income_columns,
            payload.livelihood_columns, payload.livestock_columns, payload.weight_variable,
        )

        geojson_data = _resolve_boundary_geojson(db, payload, dataset)
        merged_geojson = (
            merge_stats_with_geojson(geojson_data, stats_by_geo, payload.geo_variable, rank_field="crop_simpson_index")
            if geojson_data else None
        )
        morans_i, lisa_clusters = compute_morans_i_and_lisa(merged_geojson, value_field="crop_simpson_index")
        map_payload = build_spatial_map_payload(stats_by_geo, merged_geojson, morans_i, lisa_clusters)
        interpretation = generate_diversification_interpretation(
            stats_by_geo[0] if stats_by_geo else {"n_obs": 0}, {payload.geo_variable: stats_by_geo}
        )

        result = MicrodataAnalysisResult(
            job_id=job.id,
            summary_stats={"top_geo": stats_by_geo[0] if stats_by_geo else None},
            tables={"by_geography": stats_by_geo},
            charts=map_payload,
            geojson=merged_geojson,
            interpretation_text=interpretation,
        )
        db.add(result)
        job.status = MicrodataJobStatus.COMPLETED
        db.commit()
        db.refresh(result)

        return {
            "job_id": job.id, "status": job.status, "job_type": job.job_type,
            "summary_stats": result.summary_stats, "tables": result.tables,
            "charts": map_payload, "geojson": merged_geojson, "interpretation_text": interpretation,
        }
    except Exception as exc:
        logger.error("Spatial diversification analysis failed", exc_info=True)
        job.status = MicrodataJobStatus.FAILED
        job.error_message = str(exc)
        db.commit()
        raise HTTPException(status_code=422, detail=f"Spatial diversification analysis failed: {exc}")


@router.post("/ai-interpret", response_model=AnalysisResultResponse)
def ai_interpret(
    payload: AIInterpretRequest,
    db: Session = Depends(get_db),
    current_user=Depends(_get_user),
):
    """Regenerates (or re-fetches) the narrative interpretation for a
    completed analysis job. Currently reuses the same heuristic, data-driven
    narrative generator each analyze/* endpoint already runs inline — this
    endpoint exists so the frontend can request/re-request an interpretation
    independently of re-running the underlying statistics."""
    job = db.query(MicrodataAnalysisJob).filter(MicrodataAnalysisJob.id == payload.job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Analysis job not found")
    dataset = db.query(MicrodataDataset).filter(MicrodataDataset.id == job.dataset_id).first()
    if not dataset:
        raise HTTPException(status_code=404, detail="Dataset for this analysis not found")

    result = (
        db.query(MicrodataAnalysisResult)
        .filter(MicrodataAnalysisResult.job_id == job.id)
        .order_by(MicrodataAnalysisResult.created_at.desc())
        .first()
    )
    if not result:
        raise HTTPException(status_code=404, detail="No result available for this job yet")

    return {
        "job_id": job.id,
        "status": job.status,
        "job_type": job.job_type,
        "summary_stats": result.summary_stats,
        "tables": result.tables,
        "charts": result.charts,
        "geojson": result.geojson,
        "interpretation_text": result.interpretation_text,
    }


@router.get("/results/{job_id}", response_model=AnalysisResultResponse)
@router.get("/jobs/{job_id}", response_model=AnalysisResultResponse)
def get_analysis_job(
    job_id: UUID,
    db: Session = Depends(get_db),
    current_user=Depends(_get_user),
):
    """Fetch a previously computed analysis result by job id.
    /results/{job_id} and /jobs/{job_id} are the same endpoint."""
    job = db.query(MicrodataAnalysisJob).filter(MicrodataAnalysisJob.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Analysis job not found")

    dataset = db.query(MicrodataDataset).filter(MicrodataDataset.id == job.dataset_id).first()
    if not dataset:
        raise HTTPException(status_code=404, detail="Dataset for this analysis not found")

    result = (
        db.query(MicrodataAnalysisResult)
        .filter(MicrodataAnalysisResult.job_id == job.id)
        .order_by(MicrodataAnalysisResult.created_at.desc())
        .first()
    )

    return {
        "job_id": job.id,
        "status": job.status,
        "job_type": job.job_type,
        "summary_stats": result.summary_stats if result else None,
        "tables": result.tables if result else None,
        "charts": result.charts if result else None,
        "geojson": result.geojson if result else None,
        "interpretation_text": result.interpretation_text if result else None,
        "error_message": job.error_message,
    }
