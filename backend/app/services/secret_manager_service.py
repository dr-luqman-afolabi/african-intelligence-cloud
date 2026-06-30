from __future__ import annotations
import logging

logger = logging.getLogger(__name__)

_client = None


def _get_client():
    global _client
    if _client is None:
        from google.cloud import secretmanager
        _client = secretmanager.SecretManagerServiceClient()
    return _client


def get_secret(project_id: str, secret_id: str, version: str = "latest") -> str:
    """Fetch a secret value from GCP Secret Manager."""
    client = _get_client()
    name = f"projects/{project_id}/secrets/{secret_id}/versions/{version}"
    response = client.access_secret_version(request={"name": name})
    payload = response.payload.data.decode("utf-8")
    logger.info("Fetched secret from Secret Manager", extra={"secret_id": secret_id})
    return payload


def bootstrap_secrets(settings) -> None:
    """Overwrite critical settings fields with values from Secret Manager."""
    if not settings.use_secret_manager:
        return
    project = settings.gcp_project_id
    if not project:
        raise RuntimeError("GCP_PROJECT_ID must be set when USE_SECRET_MANAGER=true")

    try:
        settings.secret_key = get_secret(project, "aic-secret-key")
    except Exception as exc:
        logger.warning("Could not fetch aic-secret-key from Secret Manager", extra={"error": str(exc)})

    try:
        settings.database_url = get_secret(project, "aic-database-url")
    except Exception as exc:
        logger.warning("Could not fetch aic-database-url from Secret Manager", extra={"error": str(exc)})
