from __future__ import annotations

import re
import uuid
import logging
from pathlib import Path

from fastapi import UploadFile

from app.config import get_settings

logger = logging.getLogger(__name__)

ALLOWED_EXTENSIONS = {"csv", "xlsx", "dta", "sav"}

_bucket = None


def _get_bucket():
    global _bucket
    if _bucket is None:
        from google.cloud import storage
        s = get_settings()
        client = storage.Client(project=s.gcp_project_id)
        _bucket = client.bucket(s.gcs_bucket_name)
    return _bucket


def get_file_extension(filename: str) -> str:
    return filename.rsplit(".", 1)[-1].lower() if "." in filename else ""


def validate_microdata_file(file: UploadFile) -> str:
    """Raises ValueError for unsupported extensions. Returns the lowercase extension."""
    ext = get_file_extension(file.filename or "")
    if ext not in ALLOWED_EXTENSIONS:
        raise ValueError(f"Unsupported file type '.{ext}'. Allowed: {', '.join(sorted(ALLOWED_EXTENSIONS))}")
    return ext


def _slugify(value: str) -> str:
    value = value.strip().lower().replace(" ", "_")
    return re.sub(r"[^a-z0-9_\-]", "", value) or "unnamed"


def build_storage_blob_name(country: str | None, dataset_name: str, file_name: str) -> str:
    country_part = _slugify(country) if country else "unspecified"
    dataset_part = _slugify(dataset_name)
    safe_file_name = f"{uuid.uuid4().hex[:8]}_{Path(file_name).name}"
    return f"microdata/{country_part}/{dataset_part}/{safe_file_name}"


async def upload_microdata_file(file: UploadFile, country: str | None, dataset_name: str) -> tuple[str, int]:
    """Uploads the raw microdata file to Cloud Storage under microdata/{country}/{dataset_name}/{file_name}.

    Returns (storage_path, size_bytes). Raw microdata is never made public; access is
    only granted through aggregated analysis endpoints.
    """
    blob_name = build_storage_blob_name(country, dataset_name, file.filename or "upload")
    content = await file.read()

    settings = get_settings()
    if settings.storage_backend == "gcs" and settings.gcs_bucket_name:
        bucket = _get_bucket()
        blob = bucket.blob(blob_name)
        blob.upload_from_string(content, content_type="application/octet-stream")
        logger.info("Uploaded microdata file to GCS", extra={"path": blob_name, "size": len(content)})
        storage_path = f"gs://{settings.gcs_bucket_name}/{blob_name}"
    else:
        local_dir = Path(settings.upload_dir) / "microdata_raw" / Path(blob_name).parent
        local_dir.mkdir(parents=True, exist_ok=True)
        local_path = local_dir / Path(blob_name).name
        local_path.write_bytes(content)
        logger.info("Saved microdata file locally", extra={"path": str(local_path), "size": len(content)})
        storage_path = str(local_path)

    return storage_path, len(content)


def download_microdata_bytes(storage_path: str) -> bytes:
    """Reads raw bytes back from storage for server-side analysis only. Never expose this over the API."""
    if storage_path.startswith("gs://"):
        _, _, rest = storage_path.partition("gs://")
        bucket_name, _, blob_name = rest.partition("/")
        bucket = _get_bucket()
        blob = bucket.blob(blob_name)
        return blob.download_as_bytes()
    return Path(storage_path).read_bytes()
