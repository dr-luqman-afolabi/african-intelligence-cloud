"""AIC Intelligence router — conversational, automated microdata analysis.

Two endpoints power the "type a question" experience while preserving the
existing manual-click studios:

  POST /intelligence/plan   question + dataset  -> explainable analysis plan
                                                   (analysis type, mapped vars,
                                                    proposed cleaning steps)
  POST /intelligence/clean  dataset + steps     -> a new *cleaned* derived
                                                   dataset (also visible in the
                                                   shared catalog) + a report

The frontend shows the plan, the user confirms, we clean, then the existing
analysis endpoints run on the cleaned dataset and render results + the AI
policy brief. Raw microdata is never returned; only a cleaned derived file is
stored, exactly like an upload.
"""
from __future__ import annotations

import io
import logging
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.microdata import (
    MicrodataAccessStatus,
    MicrodataDataset,
    MicrodataFileType,
    MicrodataVariable,
)
from app.schemas.intelligence import (
    IntelligenceCleanRequest,
    IntelligenceCleanResponse,
    IntelligencePlan,
    IntelligencePlanRequest,
)
from app.services import aic_intelligence_service as intel
from app.services import data_cleaning_service as cleaning
from app.services.auth_service import get_current_user
from app.services.microdata_metadata_service import extract_metadata, load_dataframe
from app.services.microdata_storage_service import (
    download_microdata_bytes,
    upload_microdata_file,
)

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/intelligence", tags=["AIC Intelligence"])
security = HTTPBearer()


def _get_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db),
):
    return get_current_user(db, credentials.credentials)


def _get_dataset(db: Session, dataset_id: UUID) -> MicrodataDataset:
    dataset = db.query(MicrodataDataset).filter(MicrodataDataset.id == dataset_id).first()
    if not dataset:
        raise HTTPException(status_code=404, detail="Dataset not found")
    return dataset


def _dataset_columns(db: Session, dataset_id: UUID) -> list[dict]:
    rows = (
        db.query(MicrodataVariable)
        .filter(MicrodataVariable.dataset_id == dataset_id)
        .order_by(MicrodataVariable.variable_index)
        .all()
    )
    return [
        {"name": r.variable_name, "label": r.variable_label, "dtype": r.inferred_dtype}
        for r in rows
    ]


@router.post("/plan", response_model=IntelligencePlan)
def create_plan(
    payload: IntelligencePlanRequest,
    db: Session = Depends(get_db),
    current_user=Depends(_get_user),
):
    dataset = _get_dataset(db, payload.dataset_id)
    columns = _dataset_columns(db, dataset.id)
    if not columns:
        # Fall back to reading columns from the file itself if metadata is absent.
        try:
            df = load_dataframe(download_microdata_bytes(dataset.storage_path), dataset.file_type.value)[0]
            columns = [{"name": c, "label": None, "dtype": str(df[c].dtype)} for c in df.columns]
        except Exception:
            columns = []
    try:
        plan = intel.build_plan(payload.question, columns)
    except Exception as exc:
        logger.error("Intelligence planning failed", exc_info=True)
        raise HTTPException(status_code=422, detail=f"Could not plan analysis: {exc}")
    return plan


@router.post("/clean", response_model=IntelligenceCleanResponse)
async def clean_dataset(
    payload: IntelligenceCleanRequest,
    db: Session = Depends(get_db),
    current_user=Depends(_get_user),
):
    dataset = _get_dataset(db, payload.dataset_id)
    try:
        df, _ = load_dataframe(download_microdata_bytes(dataset.storage_path), dataset.file_type.value)
    except Exception as exc:
        raise HTTPException(status_code=422, detail=f"Could not read dataset: {exc}")

    # Resolve cleaning steps: explicit > derived from the question > basic defaults.
    if payload.cleaning_steps:
        steps = [s.model_dump(exclude_none=True) for s in payload.cleaning_steps]
    elif payload.question:
        plan = intel.build_plan(payload.question, [{"name": c} for c in df.columns])
        steps = plan.get("cleaning_steps", [])
    else:
        steps = cleaning.plan_cleaning(df, target_columns=payload.target_columns or [])

    cleaned, report = cleaning.apply_cleaning(df, steps)

    # Persist the cleaned frame as a new CSV-backed dataset (like an upload).
    csv_bytes = cleaned.to_csv(index=False).encode("utf-8")
    base = dataset.name or dataset.original_filename or "dataset"
    cleaned_name = f"{base} (AIC-cleaned)"
    filename = "aic_cleaned.csv"
    try:
        metadata = extract_metadata(csv_bytes, "csv", filename)
    except Exception as exc:
        raise HTTPException(status_code=422, detail=f"Could not profile cleaned data: {exc}")

    storage_path, size_bytes = await upload_microdata_file(
        csv_bytes, filename, dataset.country_iso3, dataset.survey_series, dataset.year
    )

    cleaned_ds = MicrodataDataset(
        project_id=dataset.project_id,
        name=cleaned_name,
        original_filename=filename,
        file_type=MicrodataFileType("csv"),
        storage_path=storage_path,
        file_size_bytes=size_bytes,
        country_iso3=dataset.country_iso3,
        survey_series=dataset.survey_series,
        year=dataset.year,
        row_count=metadata["row_count"],
        column_count=metadata["column_count"],
        missing_cells=metadata["missing_cells"],
        access_status=MicrodataAccessStatus.USER_UPLOAD,
        uploaded_by=current_user.id,
    )
    db.add(cleaned_ds)
    db.flush()
    for var in metadata["variables"]:
        db.add(MicrodataVariable(
            dataset_id=cleaned_ds.id,
            variable_name=var["variable_name"],
            variable_label=var["variable_label"],
            value_labels=var["value_labels"],
            variable_index=var["variable_index"],
            inferred_dtype=var["inferred_dtype"],
            missing_count=var["missing_count"],
        ))
    db.commit()
    db.refresh(cleaned_ds)

    return {
        "cleaned_dataset_id": cleaned_ds.id,
        "cleaned_dataset_name": cleaned_ds.name,
        "report": report,
        "row_count": cleaned_ds.row_count,
        "column_count": cleaned_ds.column_count,
    }
