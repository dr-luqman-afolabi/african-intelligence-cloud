from __future__ import annotations
import uuid
import logging
import datetime
from pathlib import Path

from fastapi import UploadFile

logger = logging.getLogger(__name__)

_bucket = None


def _get_bucket():
    global _bucket
    if _bucket is None:
        from google.cloud import storage
        from app.config import get_settings
        s = get_settings()
        client = storage.Client(project=s.gcp_project_id)
        _bucket = client.bucket(s.gcs_bucket_name)
    return _bucket


def _make_blob_name(filename: str, organization_id: str | None) -> str:
    ext = Path(filename).suffix.lstrip(".")
    folder = f"org/{organization_id}" if organization_id else "unassigned"
    return f"{folder}/{uuid.uuid4()}.{ext}"


async def upload_to_gcs(file: UploadFile, organization_id: str | None) -> tuple[str, int]:
    """Upload file to GCS. Returns (gs:// URI, file_size_bytes)."""
    from app.config import get_settings
    s = get_settings()

    content = await file.read()
    max_bytes = s.max_upload_size_mb * 1024 * 1024
    if len(content) > max_bytes:
        raise ValueError(
            f"File size {len(content) / 1024 / 1024:.1f} MB exceeds limit of {s.max_upload_size_mb} MB"
        )

    bucket = _get_bucket()
    blob_name = _make_blob_name(file.filename or "upload", organization_id)
    blob = bucket.blob(blob_name)
    blob.upload_from_string(content, content_type=file.content_type or "application/octet-stream")

    gcs_uri = f"gs://{s.gcs_bucket_name}/{blob_name}"
    logger.info("Uploaded file to GCS", extra={"uri": gcs_uri, "size": len(content)})
    return gcs_uri, len(content)


def delete_from_gcs(gcs_uri: str) -> None:
    """Delete a GCS object by its gs:// URI. Silently ignores missing blobs."""
    if not gcs_uri.startswith("gs://"):
        logger.warning("Invalid GCS URI", extra={"uri": gcs_uri})
        return

    bucket_name, _, blob_name = gcs_uri[5:].partition("/")
    try:
        from google.cloud import storage
        from app.config import get_settings
        s = get_settings()
        client = storage.Client(project=s.gcp_project_id)
        client.bucket(bucket_name).blob(blob_name).delete()
        logger.info("Deleted GCS object", extra={"uri": gcs_uri})
    except Exception as exc:
        logger.error("Failed to delete GCS object", extra={"uri": gcs_uri, "error": str(exc)})


def generate_signed_url(gcs_uri: str, expiration_minutes: int = 60) -> str:
    """Return a signed download URL for a GCS object."""
    if not gcs_uri.startswith("gs://"):
        raise ValueError(f"Invalid GCS URI: {gcs_uri}")
    _, _, blob_path = gcs_uri[5:].partition("/")
    blob = _get_bucket().blob(blob_path)
    return blob.generate_signed_url(
        expiration=datetime.timedelta(minutes=expiration_minutes),
        method="GET",
        version="v4",
    )
