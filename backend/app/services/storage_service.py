import os
import io
import zipfile
import uuid
import logging
from pathlib import Path
from fastapi import UploadFile

from app.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

ALLOWED_EXTENSIONS = {"csv", "xlsx", "xls", "json", "parquet", "dta"}


def get_file_extension(filename: str) -> str:
    return filename.rsplit(".", 1)[-1].lower() if "." in filename else ""


def extract_tabular_file_from_zip(content: bytes) -> tuple[bytes, str, str]:
    """Find the first supported tabular file inside a .zip archive and return
    (bytes, extension, filename). Picks the largest candidate so a real dataset
    is chosen over a small companion readme/codebook. Raises ValueError if none."""
    try:
        with zipfile.ZipFile(io.BytesIO(content)) as zf:
            candidates = []
            for nm in zf.namelist():
                if nm.endswith("/") or "__MACOSX" in nm or os.path.basename(nm).startswith("."):
                    continue
                e = nm.rsplit(".", 1)[-1].lower() if "." in nm else ""
                if e in ALLOWED_EXTENSIONS:
                    candidates.append((nm, e, zf.getinfo(nm).file_size))
            if not candidates:
                raise ValueError(
                    "No supported data file (" + ", ".join(sorted(ALLOWED_EXTENSIONS))
                    + ") found inside the ZIP archive."
                )
            candidates.sort(key=lambda t: t[2], reverse=True)
            nm, e, _ = candidates[0]
            return zf.read(nm), e, os.path.basename(nm)
    except zipfile.BadZipFile as exc:
        raise ValueError(f"Uploaded file is not a valid ZIP archive: {exc}")


def validate_file(file: UploadFile, max_size_bytes: int) -> None:
    """Raises ValueError for invalid extension or oversized file."""
    ext = get_file_extension(file.filename or "")
    if ext not in ALLOWED_EXTENSIONS:
        raise ValueError(f"Unsupported file type '.{ext}'. Allowed: {', '.join(sorted(ALLOWED_EXTENSIONS))}")


async def save_file_local(file: UploadFile, organization_id: str | None) -> tuple[str, int]:
    """Write uploaded file to local storage. Returns (storage_path, file_size_bytes)."""
    upload_dir = Path(settings.upload_dir)
    subfolder = str(organization_id) if organization_id else "unassigned"
    dest_dir = upload_dir / subfolder
    dest_dir.mkdir(parents=True, exist_ok=True)

    ext = get_file_extension(file.filename or "unnamed")
    stored_name = f"{uuid.uuid4()}.{ext}"
    dest_path = dest_dir / stored_name

    content = await file.read()
    max_bytes = settings.max_upload_size_mb * 1024 * 1024
    if len(content) > max_bytes:
        raise ValueError(
            f"File size {len(content) / 1024 / 1024:.1f} MB exceeds limit of {settings.max_upload_size_mb} MB"
        )

    dest_path.write_bytes(content)
    logger.info("Saved file to local storage", extra={"path": str(dest_path), "size": len(content)})
    return str(dest_path), len(content)


def delete_file_local(storage_path: str) -> None:
    """Delete a locally stored file. Silently ignores missing files."""
    try:
        Path(storage_path).unlink(missing_ok=True)
        logger.info("Deleted local file", extra={"path": storage_path})
    except Exception as exc:
        logger.error("Failed to delete local file", extra={"path": storage_path, "error": str(exc)})


async def save_file_gcs(file: UploadFile, organization_id: str | None) -> tuple[str, int]:
    """Upload file to GCS. Delegates to gcs_service."""
    from app.services.gcs_service import upload_to_gcs
    return await upload_to_gcs(file, organization_id)


def delete_file_gcs(storage_path: str) -> None:
    """Delete a file from GCS. Delegates to gcs_service."""
    from app.services.gcs_service import delete_from_gcs
    delete_from_gcs(storage_path)


# ── Unified interface ────────────────────────────────────────────────────────

async def save_upload(file: UploadFile, organization_id: str | None) -> tuple[str, int]:
    """Save file using the configured storage backend. Returns (storage_path, file_size_bytes)."""
    if settings.storage_backend == "gcs":
        return await save_file_gcs(file, organization_id)
    return await save_file_local(file, organization_id)


def delete_upload(storage_path: str) -> None:
    """Delete a stored file using the configured backend."""
    if settings.storage_backend == "gcs":
        delete_file_gcs(storage_path)
    else:
        delete_file_local(storage_path)
