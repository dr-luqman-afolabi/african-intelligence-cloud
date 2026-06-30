"""LSMS connector — Living Standards Measurement Study (World Bank)."""
from __future__ import annotations

import logging
import time
import requests

from app.connectors.base import BaseConnector, ConnectorMetadata, HealthStatus

logger = logging.getLogger(__name__)

# LSMS data is distributed via the World Bank Microdata Library catalog API
_CATALOG_BASE = "https://microdata.worldbank.org/index.php/api/catalog"

_SUPPORTED_COUNTRIES = ["NGA", "ETH", "UGA", "TZA", "MLI", "NER", "BFA"]


class LSMSConnector(BaseConnector):
    source_id = "unps_lsms"

    def get_metadata(self) -> ConnectorMetadata:
        return ConnectorMetadata(
            source_id=self.source_id,
            source_name="LSMS — Living Standards Measurement Study",
            description="World Bank household survey microdata catalogue for African LSMS surveys.",
            base_url=_CATALOG_BASE,
            license_category="B",
            update_frequency="irregular",
            supported_countries=_SUPPORTED_COUNTRIES,
        )

    def health_check(self) -> HealthStatus:
        url = f"{_CATALOG_BASE}/search"
        params = {"keyword": "LSMS Nigeria", "format": "json", "per_page": 1}
        try:
            t0 = time.monotonic()
            resp = requests.get(url, params=params, timeout=10)
            latency = round((time.monotonic() - t0) * 1000, 1)
            resp.raise_for_status()
            return HealthStatus(source_id=self.source_id, healthy=True, latency_ms=latency, message="Catalog API OK")
        except Exception as exc:
            return HealthStatus(source_id=self.source_id, healthy=False, message=str(exc))

    def fetch(self, **kwargs) -> list[dict]:
        """
        Returns catalog-level metadata for available LSMS surveys.
        Microdata files require authenticated download from the Microdata Library;
        the connector returns survey catalogue records rather than indicators.
        """
        raw: list[dict] = []
        for iso3 in _SUPPORTED_COUNTRIES:
            url = f"{_CATALOG_BASE}/search"
            params = {"keyword": f"LSMS {iso3}", "format": "json", "per_page": 20}
            try:
                resp = requests.get(url, params=params, timeout=20)
                resp.raise_for_status()
                for survey in resp.json().get("result", {}).get("rows", []):
                    raw.append({
                        "iso3": iso3,
                        "indicator_code": f"LSMS_CATALOG_{survey.get('id', '')}",
                        "year": survey.get("year_start"),
                        "value": 1,
                        "unit": "survey",
                        "survey_title": survey.get("title", ""),
                    })
            except Exception as exc:
                logger.debug("LSMS catalog search error for %s: %s", iso3, exc)
        return raw

    def normalise(self, raw: list[dict]) -> list[dict]:
        return [
            {
                "country_iso3": r["iso3"],
                "indicator_code": r["indicator_code"],
                "year": int(r["year"]) if r.get("year") else None,
                "value": float(r["value"]),
                "unit": r.get("unit", ""),
                "data_source": "LSMS — World Bank Microdata Library",
                "source_id": self.source_id,
            }
            for r in raw
            if r.get("iso3") and r.get("year")
        ]


from app.services.connector_service import register_connector
register_connector(LSMSConnector())
