"""NISR connector — National Institute of Statistics of Rwanda."""
from __future__ import annotations

import logging
import time
import requests

from app.connectors.base import BaseConnector, ConnectorMetadata, HealthStatus

logger = logging.getLogger(__name__)

# NISR publishes data via the Rwanda OpenData portal and NISR API
_BASE = "https://opendata.statistics.gov.rw/api"

# These are the survey series available from NISR
_DATASETS = {
    "EICV": "Integrated Household Living Conditions Survey",
    "LFS": "Labour Force Survey",
    "CENSUS": "Population and Housing Census",
    "DHS_RW": "Rwanda Demographic and Health Survey",
}

_ISO3 = "RWA"


class NISRConnector(BaseConnector):
    source_id = "rwanda_nisr"

    def get_metadata(self) -> ConnectorMetadata:
        return ConnectorMetadata(
            source_id=self.source_id,
            source_name="NISR Rwanda",
            description="National Institute of Statistics Rwanda — EICV, LFS, Census, and DHS surveys.",
            base_url=_BASE,
            license_category="B",
            update_frequency="triennial",
            supported_countries=[_ISO3],
        )

    def health_check(self) -> HealthStatus:
        url = f"{_BASE}/3/action/package_search"
        params = {"q": "EICV", "rows": 1}
        try:
            t0 = time.monotonic()
            resp = requests.get(url, params=params, timeout=10)
            latency = round((time.monotonic() - t0) * 1000, 1)
            if resp.status_code == 200:
                return HealthStatus(source_id=self.source_id, healthy=True, latency_ms=latency, message="OpenData portal OK")
        except Exception:
            pass
        # Fallback: check NISR homepage returns 200
        try:
            t0 = time.monotonic()
            resp = requests.get("https://www.statistics.gov.rw", timeout=8)
            latency = round((time.monotonic() - t0) * 1000, 1)
            return HealthStatus(
                source_id=self.source_id,
                healthy=resp.status_code == 200,
                latency_ms=latency,
                message=f"NISR homepage HTTP {resp.status_code}",
            )
        except Exception as exc:
            return HealthStatus(source_id=self.source_id, healthy=False, message=str(exc))

    def fetch(self, **kwargs) -> list[dict]:
        """
        Returns catalogue records from the Rwanda OpenData CKAN portal.
        Microdata require offline download; this returns survey metadata.
        """
        raw: list[dict] = []
        for dataset_key, dataset_name in _DATASETS.items():
            url = f"{_BASE}/3/action/package_search"
            params = {"q": dataset_key, "rows": 10}
            try:
                resp = requests.get(url, params=params, timeout=15)
                if resp.status_code != 200:
                    continue
                for pkg in resp.json().get("result", {}).get("results", []):
                    extras = {e["key"]: e.get("value") for e in pkg.get("extras", [])}
                    year_str = extras.get("year") or pkg.get("metadata_created", "")[:4]
                    raw.append({
                        "iso3": _ISO3,
                        "indicator_code": f"NISR_{dataset_key}_{pkg.get('id', '')[:8]}",
                        "year": int(year_str) if year_str and year_str.isdigit() else None,
                        "value": 1,
                        "unit": "survey",
                        "dataset_name": pkg.get("title", dataset_name),
                    })
            except Exception as exc:
                logger.debug("NISR fetch error for %s: %s", dataset_key, exc)
        return raw

    def normalise(self, raw: list[dict]) -> list[dict]:
        return [
            {
                "country_iso3": r["iso3"],
                "indicator_code": r["indicator_code"],
                "year": r["year"],
                "value": float(r["value"]),
                "unit": r.get("unit", ""),
                "data_source": "NISR Rwanda",
                "source_id": self.source_id,
            }
            for r in raw
            if r.get("year")
        ]


from app.services.connector_service import register_connector
register_connector(NISRConnector())
