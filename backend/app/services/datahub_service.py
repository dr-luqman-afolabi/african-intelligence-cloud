"""DataHub GMS REST emitter service.

Pushes dataset and schema metadata from AIC sync jobs to DataHub's
Generalized Metadata Service (GMS) REST API using the minimal REST envelope.
No datahub-ingestion SDK dependency — uses plain HTTP so the core backend
stays lightweight.
"""
from __future__ import annotations

import hashlib
import json
import logging
import time
from datetime import datetime, timezone

import requests

from app.config import get_settings

logger = logging.getLogger(__name__)

_GMS_TIMEOUT = 10  # seconds per request


def _gms_url() -> str | None:
    """Return the DataHub GMS base URL from settings, or None if not configured."""
    s = get_settings()
    return getattr(s, "datahub_gms_url", None) or None


def _headers() -> dict[str, str]:
    s = get_settings()
    token = getattr(s, "datahub_token", None) or ""
    h = {"Content-Type": "application/json"}
    if token:
        h["Authorization"] = f"Bearer {token}"
    return h


# ---------------------------------------------------------------------------
# URN helpers
# ---------------------------------------------------------------------------

def _dataset_urn(source_id: str, platform: str = "aic") -> str:
    return f"urn:li:dataset:(urn:li:dataPlatform:{platform},{source_id},PROD)"


def _schema_hash(fields: list[str]) -> str:
    return hashlib.md5(",".join(sorted(fields)).encode()).hexdigest()[:8]


# ---------------------------------------------------------------------------
# Core emit helpers
# ---------------------------------------------------------------------------

def _emit_aspect(urn: str, aspect_name: str, aspect: dict) -> bool:
    """POST a single aspect to DataHub GMS /aspects endpoint. Returns True on success."""
    gms = _gms_url()
    if not gms:
        logger.debug("DataHub GMS URL not configured — skipping emit for %s", urn)
        return False

    url = f"{gms.rstrip('/')}/aspects?action=ingestProposal"
    payload = {
        "proposal": {
            "entityType": "dataset",
            "entityUrn": urn,
            "changeType": "UPSERT",
            "aspectName": aspect_name,
            "aspect": {
                "value": json.dumps(aspect),
                "contentType": "application/json",
            },
        }
    }
    try:
        resp = requests.post(url, json=payload, headers=_headers(), timeout=_GMS_TIMEOUT)
        resp.raise_for_status()
        logger.info("DataHub aspect emitted: urn=%s aspect=%s", urn, aspect_name)
        return True
    except Exception as exc:
        logger.warning("DataHub emit failed: urn=%s aspect=%s error=%s", urn, aspect_name, exc)
        return False


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def push_dataset_metadata(source_id: str, records: list[dict], source_name: str = "") -> dict:
    """
    Emit dataset-level metadata to DataHub for a completed sync.
    Returns a dict with counts of successful/failed aspect emits.
    """
    urn = _dataset_urn(source_id)
    now_ms = int(time.time() * 1000)
    success, failed = 0, 0

    # 1. DatasetProperties aspect
    countries = sorted({r.get("country_iso3", "") for r in records if r.get("country_iso3")})
    indicators = sorted({r.get("indicator_code", "") for r in records if r.get("indicator_code")})
    years = sorted({r.get("year") for r in records if r.get("year") is not None})

    props = {
        "customProperties": {
            "source_id": source_id,
            "countries": ",".join(countries[:20]),
            "indicators": ",".join(indicators[:20]),
            "year_range": f"{min(years)}-{max(years)}" if years else "",
            "record_count": str(len(records)),
            "last_synced": datetime.now(timezone.utc).isoformat(),
        },
        "name": source_name or source_id,
        "description": f"AIC connector data for {source_id}. "
                       f"Countries: {len(countries)}. Indicators: {len(indicators)}.",
        "tags": [],
    }
    ok = _emit_aspect(urn, "datasetProperties", props)
    success += int(ok); failed += int(not ok)

    # 2. SchemaMetadata aspect (inferred from canonical normalised fields)
    schema_fields = ["country_iso3", "indicator_code", "year", "value", "unit",
                     "data_source", "source_id"]
    schema = {
        "schemaName": f"{source_id}_schema",
        "platform": "urn:li:dataPlatform:aic",
        "version": 0,
        "hash": _schema_hash(schema_fields),
        "platformSchema": {
            "com.linkedin.schema.OtherSchema": {"rawSchema": ",".join(schema_fields)}
        },
        "fields": [
            {
                "fieldPath": f,
                "nullable": True,
                "type": {"type": {"com.linkedin.schema.StringType": {}}},
                "nativeDataType": "string",
            }
            for f in schema_fields
        ],
    }
    ok = _emit_aspect(urn, "schemaMetadata", schema)
    success += int(ok); failed += int(not ok)

    # 3. DatasetUsageStatistics aspect
    stats = {
        "timestampMillis": now_ms,
        "eventGranularity": {"unit": "DAY", "multiple": 1},
        "rowCount": len(records),
        "columnCount": len(schema_fields),
    }
    ok = _emit_aspect(urn, "datasetUsageStatistics", stats)
    success += int(ok); failed += int(not ok)

    return {"urn": urn, "aspects_success": success, "aspects_failed": failed}


def push_lineage(source_id: str, upstream_source_ids: list[str]) -> bool:
    """Emit upstream lineage edges for a dataset to DataHub."""
    urn = _dataset_urn(source_id)
    lineage = {
        "upstreams": [
            {
                "dataset": _dataset_urn(uid),
                "type": "TRANSFORMED",
            }
            for uid in upstream_source_ids
        ]
    }
    return _emit_aspect(urn, "upstreamLineage", lineage)
