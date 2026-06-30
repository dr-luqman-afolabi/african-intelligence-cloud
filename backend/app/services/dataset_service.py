import logging
from uuid import UUID
from datetime import datetime, timezone

from fastapi import UploadFile, HTTPException
from sqlalchemy.orm import Session

from app.database import SessionLocal
from app.models.dataset import UploadedDataset, DatasetColumn, DatasetProfile, DatasetStatus, AnalysisJob
from app.models.audit_log import AuditLog
from app.models.user import User
from app.services.storage_service import validate_file, save_upload, delete_upload, get_file_extension
from app.services.profiling_service import run_profiling

logger = logging.getLogger(__name__)


def _write_audit(db: Session, user_id: UUID, action: str, resource_id: str, ip: str = "", agent: str = "") -> None:
    log = AuditLog(
        user_id=user_id,
        action=action,
        resource="dataset",
        resource_id=resource_id,
        ip_address=ip,
        user_agent=agent,
    )
    db.add(log)


async def upload_dataset(
    db: Session,
    file: UploadFile,
    name: str,
    description: str | None,
    privacy: str,
    tags: list[str] | None,
    current_user: User,
    client_ip: str = "",
    user_agent: str = "",
) -> UploadedDataset:
    """Validate, store, and persist a new dataset record."""
    from app.models.dataset import DatasetPrivacy

    # Validate extension and size limits before reading
    validate_file(file, max_size_bytes=0)  # size checked inside save_upload

    org_id = current_user.organization_id
    storage_path, file_size = await save_upload(file, str(org_id) if org_id else None)
    ext = get_file_extension(file.filename or "unnamed")

    dataset = UploadedDataset(
        name=name,
        description=description,
        original_filename=file.filename or "unknown",
        file_extension=ext,
        file_size_bytes=file_size,
        storage_path=storage_path,
        privacy=DatasetPrivacy(privacy),
        status=DatasetStatus.UPLOADED,
        tags=tags or [],
        uploaded_by=current_user.id,
        organization_id=org_id,
    )
    db.add(dataset)
    db.commit()
    db.refresh(dataset)

    _write_audit(db, current_user.id, "dataset.upload", str(dataset.id), client_ip, user_agent)
    db.commit()

    logger.info("Dataset uploaded", extra={"dataset_id": str(dataset.id), "user": str(current_user.id)})
    return dataset


def get_datasets_for_user(
    db: Session,
    current_user: User,
    page: int = 1,
    page_size: int = 20,
) -> tuple[list[UploadedDataset], int]:
    """Return datasets visible to the current user (own + org + public)."""
    from sqlalchemy import or_
    from app.models.dataset import DatasetPrivacy

    query = db.query(UploadedDataset).filter(
        or_(
            UploadedDataset.uploaded_by == current_user.id,
            UploadedDataset.privacy == DatasetPrivacy.PUBLIC,
            (
                (UploadedDataset.organization_id == current_user.organization_id)
                & (current_user.organization_id.isnot(None) if hasattr(current_user.organization_id, "isnot") else False)
                & (UploadedDataset.privacy == DatasetPrivacy.ORGANIZATION)
            )
            if current_user.organization_id
            else False,
        )
    ).order_by(UploadedDataset.created_at.desc())

    total = query.count()
    items = query.offset((page - 1) * page_size).limit(page_size).all()
    return items, total


def get_dataset_by_id(db: Session, dataset_id: UUID, current_user: User) -> UploadedDataset:
    """Return a single dataset if the user has read access."""
    from app.models.dataset import DatasetPrivacy

    dataset = db.query(UploadedDataset).filter(UploadedDataset.id == dataset_id).first()
    if not dataset:
        raise HTTPException(status_code=404, detail="Dataset not found")

    can_read = (
        dataset.uploaded_by == current_user.id
        or dataset.privacy == DatasetPrivacy.PUBLIC
        or (
            dataset.privacy == DatasetPrivacy.ORGANIZATION
            and dataset.organization_id is not None
            and dataset.organization_id == current_user.organization_id
        )
    )
    if not can_read:
        raise HTTPException(status_code=403, detail="Access denied")

    return dataset


def delete_dataset(db: Session, dataset_id: UUID, current_user: User, ip: str = "", user_agent: str = "") -> None:
    """Delete a dataset record and its stored file. Only the uploader may delete."""
    dataset = get_dataset_by_id(db, dataset_id, current_user)
    if dataset.uploaded_by != current_user.id:
        raise HTTPException(status_code=403, detail="Only the uploader can delete this dataset")

    storage_path = dataset.storage_path
    _write_audit(db, current_user.id, "dataset.delete", str(dataset_id), ip, user_agent)
    db.delete(dataset)
    db.commit()

    try:
        delete_upload(storage_path)
    except Exception as exc:
        logger.error("File deletion failed after DB delete", extra={"path": storage_path, "error": str(exc)})

    logger.info("Dataset deleted", extra={"dataset_id": str(dataset_id)})


def trigger_profiling(db: Session, dataset_id: UUID, current_user: User) -> UploadedDataset:
    """Mark dataset as profiling and enqueue background job."""
    dataset = get_dataset_by_id(db, dataset_id, current_user)

    if dataset.status == DatasetStatus.PROFILING:
        raise HTTPException(status_code=409, detail="Profiling already in progress")

    dataset.status = DatasetStatus.PROFILING
    job = AnalysisJob(dataset_id=dataset_id, job_type="profile", status="queued")
    db.add(job)
    db.commit()
    db.refresh(dataset)
    return dataset


def _run_profiling_background(dataset_id: str) -> None:
    """Background task: profile a dataset and persist results."""
    db = SessionLocal()
    try:
        dataset = db.query(UploadedDataset).filter(UploadedDataset.id == dataset_id).first()
        if not dataset:
            return

        job = (
            db.query(AnalysisJob)
            .filter(AnalysisJob.dataset_id == dataset_id, AnalysisJob.status == "queued")
            .order_by(AnalysisJob.created_at.desc())
            .first()
        )

        started_at = datetime.now(timezone.utc)
        if job:
            job.status = "running"
            job.started_at = started_at
            db.commit()

        try:
            result = run_profiling(dataset.storage_path, dataset.file_extension)
            summary = result["summary"]
            columns_data = result["columns"]

            # Upsert profile
            existing_profile = db.query(DatasetProfile).filter(DatasetProfile.dataset_id == dataset_id).first()
            if existing_profile:
                db.delete(existing_profile)
                db.flush()

            profile = DatasetProfile(
                dataset_id=dataset.id,
                row_count=summary["row_count"],
                column_count=summary["column_count"],
                missing_cells=summary["missing_cells"],
                missing_cells_pct=summary["missing_cells_pct"],
                duplicate_rows=summary["duplicate_rows"],
                numeric_columns=summary["numeric_columns"],
                categorical_columns=summary["categorical_columns"],
                datetime_columns=summary["datetime_columns"],
                profiling_duration_ms=summary["profiling_duration_ms"],
            )
            db.add(profile)

            # Replace column metadata
            db.query(DatasetColumn).filter(DatasetColumn.dataset_id == dataset_id).delete()
            for col_data in columns_data:
                col = DatasetColumn(dataset_id=dataset.id, **col_data)
                db.add(col)

            dataset.status = DatasetStatus.PROFILED
            dataset.row_count = summary["row_count"]
            dataset.column_count = summary["column_count"]

            if job:
                job.status = "completed"
                job.completed_at = datetime.now(timezone.utc)
                job.result_summary = {"rows": summary["row_count"], "cols": summary["column_count"]}

        except Exception as exc:
            logger.error("Profiling failed", extra={"dataset_id": dataset_id, "error": str(exc)})
            dataset.status = DatasetStatus.FAILED
            if job:
                job.status = "failed"
                job.error_message = str(exc)
                job.completed_at = datetime.now(timezone.utc)

        db.commit()
    finally:
        db.close()
