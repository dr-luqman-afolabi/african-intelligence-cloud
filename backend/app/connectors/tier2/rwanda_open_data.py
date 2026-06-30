"""Rwanda Open Data connector.

Queries the Rwanda Open Data Portal (opendata.rw) via its CKAN REST API.
Returns dataset metadata and indicator records published by the Government
of Rwanda, NISR, and affiliated institutions.
"""
from __future__ import annotations

import logging
import time
import requests

from app.connectors.base import BaseConnector, ConnectorMetadata, HealthStatus

logger = logging.getLogger(__name__)

_BASE = "https://opendata.rw"
_CKAN_API = f"{_BASE}/api/3/action"

_ISO3 = "RWA"


class RwandaOpenDataConnector(BaseConnector):
    source_id = "rwanda_open_data"

    def get_metadata(self) -> ConnectorMetadata:
        return ConnectorMetadata(
            source_id=self.source_id,
            source_name="Rwanda Open Data Portal",
            description=(
                "Government of Rwanda open data portal (CKAN) — economic, social, "
                "demographic, and administrative datasets published by NISR and ministries."
            ),
            base_url=_BASE,
            license_category="A",
            update_frequency="irregular",
            supported_countries=[_ISO3],
        )

    def health_check(self) -> HealthStatus:
        url = f"{_CKAN_API}/site_read"
        try:
            t0 = time.monotonic()
            resp = requests.get(url, timeout=10)
            latency = round((time.monotonic() - t0) * 1000, 1)
            if resp.status_code == 200 and resp.json().get("success"):
                return HealthStatus(
                    source_id=self.source_id,
                    healthy=True,
                    latency_ms=latency,
                    message="CKAN API OK",
                )
            return HealthStatus(
                source_id=self.source_id,
                healthy=False,
                message=f"CKAN site_read failed: HTTP {resp.status_code}",
            )
        except Exception as exc:
            return HealthStatus(source_id=self.source_id, healthy=False, message=str(exc))

    def fetch(self, **kwargs) -> list[dict]:
        """Fetch dataset list from CKAN package_search."""
        raw: list[dict] = []
        rows = 100
        start = 0

        while True:
            url = f"{_CKAN_API}/package_search"
            params = {"rows": rows, "start": start, "sort": "metadata_modified desc"}
            try:
                resp = requests.get(url, params=params, timeout=20)
                resp.raise_for_status()
                body = resp.json()
                if not body.get("success"):
                    break
                results = body["result"].get("results", [])
                if not results:
                    break
                for pkg in results:
                    # Attempt to extract a year from metadata_modified
                    year = None
                    modified = pkg.get("metadata_modified", "")
                    if modified:
                        try:
                            year = int(modified[:4])
                        except ValueError:
                            pass

                    raw.append({
                        "iso3": _ISO3,
                        "indicator_code": f"RWA_ODP_{pkg.get('name', pkg.get('id', ''))}",
                        "year": year,
                        "value": 1,
                        "unit": "dataset",
                        "title": pkg.get("title", ""),
                        "pkg_id": pkg.get("id", ""),
                    })
                start += rows
                if start >= body["result"].get("count", 0):
                    break
            except Exception as exc:
                logger.debug("Rwanda ODP fetch error (start=%d): %s", start, exc)
                break

        return raw

    def normalise(self, raw: list[dict]) -> list[dict]:
        out = []
        for r in raw:
            if not r.get("year"):
                continue
            out.append({
                "country_iso3": _ISO3,
                "indicator_code": r["indicator_code"],
                "year": r["year"],
                "value": float(r["value"]),
                "unit": r.get("unit", "dataset"),
                "data_source": "Rwanda Open Data Portal",
                "source_id": self.source_id,
                "metadata": {
                    "dataset_title": r.get("title", ""),
                    "ckan_id": r.get("pkg_id", ""),
                },
            })
        return out


from app.services.connector_service import register_connector
register_connector(RwandaOpenDataConnector())
