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
    AnalysisResultResponse,
    MicrodataDatasetListResponse,
    MicrodataDatasetResponse,
    MicrodataVariableResponse,
    PovertyAnalysisRequest,
    SpatialPovertyAnalysisRequest,
)
from app.services.auth_service import get_current_user
from app.services.microdata_metadata_service import extract_metadata, load_dataframe
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
)
from app.services.spatial_boundary_service import get_boundaries_geojson

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
    if dataset.uploaded_by != current_user.id:
        raise HTTPException(status_code=403, detail="You do not have access to this dataset")
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
    """Uploads a raw microdata file (.csv, .xlsx, .dta, .sav), stores it in Cloud Storage,
    and extracts variable-level metadata. Raw microdata is never made public; only
    aggregated analysis results are ever returned via the analyze endpoints.
    """
    try:
        ext = validate_microdata_file(file)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))

    content = await file.read()
    await file.seek(0)

    try:
        metadata = extract_metadata(content, ext, file.filename or name)
    except Exception as exc:
        logger.error("Metadata extraction failed", exc_info=True)
        raise HTTPException(status_code=422, detail=f"Could not parse microdata file: {exc}")

    await file.seek(0)
    country_guess = country_iso3 or metadata.get("detected_country")
    storage_path, size_bytes = await upload_microdata_file(file, country_guess, name)

    dataset = MicrodataDataset(
        project_id=UUID(project_id) if project_id else None,
        name=name,
        original_filename=file.filename or name,
        file_type=MicrodataFileType(ext),
        storage_path=storage_path,
        file_size_bytes=size_bytes,
        country_iso3=country_guess,
        survey_series=metadata.get("detected_series"),
        year=metadata.get("detected_year"),
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
    query = db.query(MicrodataDataset).filter(MicrodataDataset.uploaded_by == current_user.id)
    total = query.count()
    items = query.order_by(MicrodataDataset.created_at.desc()).offset(skip).limit(limit).all()
    return {"items": items, "total": total}


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

        geojson_data = None
        if payload.geojson_boundary_file:
            try:
                geojson_data = json.loads(payload.geojson_boundary_file)
            except (json.JSONDecodeError, TypeError) as exc:
                logger.warning("Could not parse geojson_boundary_file: %s", exc)
        elif payload.country_iso3 and payload.admin_level:
            try:
                geojson_data = get_boundaries_geojson(db, payload.country_iso3, payload.admin_level)
            except HTTPException as exc:
                logger.warning("No persisted boundaries for %s/%s: %s", payload.country_iso3, payload.admin_level, exc.detail)

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


@router.get("/jobs/{job_id}", response_model=AnalysisResultResponse)
def get_analysis_job(
    job_id: UUID,
    db: Session = Depends(get_db),
    current_user=Depends(_get_user),
):
    """Fetch a previously computed poverty or spatial-poverty analysis result by job id."""
    job = db.query(MicrodataAnalysisJob).filter(MicrodataAnalysisJob.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Analysis job not found")

    dataset = db.query(MicrodataDataset).filter(MicrodataDataset.id == job.dataset_id).first()
    if not dataset or dataset.uploaded_by != current_user.id:
        raise HTTPException(status_code=403, detail="You do not have access to this analysis")

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
