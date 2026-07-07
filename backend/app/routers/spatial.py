from __future__ import annotations

import logging
from uuid import UUID

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.microdata import MicrodataAnalysisJob, MicrodataAnalysisResult, MicrodataDataset
from app.services import spatial_boundary_service
from app.services.auth_service import get_current_user

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/spatial", tags=["Spatial / GIS"])
security = HTTPBearer()

_ADMIN_LEVELS = {"ADM0", "ADM1", "ADM2", "ADM3"}
_SOURCES = {"gadm", "hdx", "ocha_cod_ab", "natural_earth", "custom_upload"}


def _get_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db),
):
    return get_current_user(db, credentials.credentials)


@router.post("/boundaries/upload", status_code=201)
async def upload_boundaries(
    file: UploadFile = File(...),
    country: str = Form(...),
    iso3: str = Form(...),
    admin_level: str = Form(...),
    source: str = Form("custom_upload"),
    year: int | None = Form(None),
    license: str | None = Form(None),
    name_field: str | None = Form(None),
    code_field: str | None = Form(None),
    db: Session = Depends(get_db),
    current_user=Depends(_get_user),
):
    """Ingest a boundary file (GeoJSON or zipped Shapefile) from GADM, HDX/OCHA COD-AB,
    Natural Earth, or a custom source. Reusable across every future analysis for that
    country/admin level — no need to paste GeoJSON into every request.
    """
    if admin_level not in _ADMIN_LEVELS:
        raise HTTPException(status_code=422, detail=f"admin_level must be one of {sorted(_ADMIN_LEVELS)}")
    if source not in _SOURCES:
        raise HTTPException(status_code=422, detail=f"source must be one of {sorted(_SOURCES)}")
    if len(iso3) != 3:
        raise HTTPException(status_code=422, detail="iso3 must be a 3-letter ISO country code")

    content = await file.read()
    return spatial_boundary_service.ingest_boundary_file(
        db=db,
        content=content,
        filename=file.filename or "upload",
        country=country,
        iso3=iso3,
        admin_level=admin_level,
        source=source,
        year=year,
        license=license,
        name_field=name_field,
        code_field=code_field,
        current_user=current_user,
    )


@router.get("/boundaries")
def list_boundaries(
    iso3: str | None = None,
    admin_level: str | None = None,
    db: Session = Depends(get_db),
):
    """List boundary metadata (no geometry payload) across all African countries, optionally filtered."""
    items, total = spatial_boundary_service.list_boundaries(db, iso3=iso3, admin_level=admin_level)
    return {"items": items, "total": total}


@router.get("/boundaries/{country_iso3}")
def get_country_boundaries(
    country_iso3: str,
    admin_level: str | None = None,
    db: Session = Depends(get_db),
):
    """Return map-ready GeoJSON boundaries for a single country, optionally filtered by admin level."""
    return spatial_boundary_service.get_boundaries_geojson(db, country_iso3, admin_level=admin_level)


@router.get("/results/{analysis_id}")
def get_analysis_result(
    analysis_id: UUID,
    db: Session = Depends(get_db),
    current_user=Depends(_get_user),
):
    """Fetch a previously computed spatial poverty analysis result.

    `analysis_id` is the job id returned by POST /microdata/analyze/spatial-poverty
    (results are persisted via the shared microdata analysis job/result tables).
    """
    job = db.query(MicrodataAnalysisJob).filter(MicrodataAnalysisJob.id == analysis_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Analysis result not found")

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
        "analysis_id": job.id,
        "status": job.status,
        "job_type": job.job_type,
        "summary_stats": result.summary_stats if result else None,
        "tables": result.tables if result else None,
        "charts": result.charts if result else None,
        "geojson": result.geojson if result else None,
        "interpretation_text": result.interpretation_text if result else None,
        "error_message": job.error_message,
    }
