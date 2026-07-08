from __future__ import annotations

import re
import uuid
import logging
from pathlib import Path

from fastapi import UploadFile

from app.config import get_settings

logger = logging.getLogger(__name__)

ALLOWED_EXTENSIONS = {"csv", "xlsx", "dta", "sav"}
# .zip is accepted at upload time only — extract_supported_file_from_zip()
# pulls the real data file out of it before storage/analysis ever see it, so
# nothing downstream needs to know about zip archives at all.
ALLOWED_UPLOAD_EXTENSIONS = ALLOWED_EXTENSIONS | {"zip"}

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
    """Raises ValueError for unsupported extensions. Returns the lowercase
    extension, which may be "zip" — callers must extract the real data file
    (see microdata_metadata_service.extract_supported_file_from_zip) before
    treating the upload as a dataset."""
    ext = get_file_extension(file.filename or "")
    if ext not in ALLOWED_UPLOAD_EXTENSIONS:
        raise ValueError(
            f"Unsupported file type '.{ext}'. Allowed: {', '.join(sorted(ALLOWED_UPLOAD_EXTENSIONS))}"
        )
    return ext


def _slugify(value: str) -> str:
    value = value.strip().lower().replace(" ", "_")
    return re.sub(r"[^a-z0-9_\-]", "", value) or "unnamed"


def build_storage_blob_name(
    country: str | None, survey: str | None, year: int | None, file_name: str
) -> str:
    """microdata/{country}/{survey}/{year}/{filename} — country/survey/year
    default to "unspecified"/"unknown" when not detected or provided, so the
    path is always well-formed."""
    country_part = _slugify(country) if country else "unspecified"
    survey_part = _slugify(survey) if survey else "unspecified"
    year_part = str(year) if year else "unknown"
    safe_file_name = f"{uuid.uuid4().hex[:8]}_{Path(file_name).name}"
    return f"microdata/{country_part}/{survey_part}/{year_part}/{safe_file_name}"


async def upload_microdata_file(
    content: bytes,
    file_name: str,
    country: str | None,
    survey: str | None = None,
    year: int | None = None,
) -> tuple[str, int]:
    """Uploads raw microdata bytes to Cloud Storage under
    microdata/{country}/{survey}/{year}/{filename}.

    Takes raw bytes (not an UploadFile) so a file extracted from a ZIP
    upload can be stored the same way as a directly-uploaded file. Returns
    (storage_path, size_bytes). Raw microdata is never made public; access
    is only granted through aggregated analysis endpoints.
    """
    blob_name = build_storage_blob_name(country, survey, year, file_name)

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
