"""IHSN/NADA connector — International Household Survey Network metadata catalog.

NADA (National Data Archive) is the flagship data dissemination platform of
the IHSN. The catalog at catalog.ihsn.org exposes a REST API that returns
survey metadata for hundreds of national household surveys across Africa.
No authentication is required for catalogue-level records.
"""
from __future__ import annotations

import logging
import time
import requests

from app.connectors.base import BaseConnector, ConnectorMetadata, HealthStatus

logger = logging.getLogger(__name__)

_BASE = "https://catalog.ihsn.org"
_API = f"{_BASE}/index.php/api/catalog"

_COUNTRIES = [
    "NGA", "ETH", "KEN", "GHA", "TZA", "UGA", "RWA", "MOZ", "ZMB",
    "CMR", "SEN", "CIV", "MDG", "NER", "MLI", "BFA", "MWI", "ZWE",
    "ZAF", "SDN", "BWA", "NAM", "SLE", "LBR", "BEN", "TGO", "BDI",
    "COD", "COG", "CAF", "TCD", "MRT", "GMB", "DJI", "ERI", "SOM",
]


class IHSNNADAConnector(BaseConnector):
    source_id = "ihsn_nada"

    def get_metadata(self) -> ConnectorMetadata:
        return ConnectorMetadata(
            source_id=self.source_id,
            source_name="IHSN/NADA Survey Catalog",
            description=(
                "International Household Survey Network NADA catalog — "
                "national household survey metadata for African countries."
            ),
            base_url=_BASE,
            license_category="B",
            update_frequency="continuous",
            supported_countries=_COUNTRIES,
        )

    def health_check(self) -> HealthStatus:
        url = f"{_API}/search"
        params = {"keyword": "Africa", "format": "json", "per_page": 1}
        try:
            t0 = time.monotonic()
            resp = requests.get(url, params=params, timeout=10)
            latency = round((time.monotonic() - t0) * 1000, 1)
            if resp.status_code == 200:
                return HealthStatus(
                    source_id=self.source_id,
                    healthy=True,
                    latency_ms=latency,
                    message="IHSN NADA API OK",
                )
            return HealthStatus(source_id=self.source_id, healthy=False,
                                message=f"HTTP {resp.status_code}")
        except Exception as exc:
            return HealthStatus(source_id=self.source_id, healthy=False, message=str(exc))

    def fetch(self, **kwargs) -> list[dict]:
        """Query IHSN catalog for African household surveys."""
        raw: list[dict] = []
        for iso3 in _COUNTRIES:
            url = f"{_API}/search"
            params = {
                "country_iso": iso3,
                "format": "json",
                "per_page": 50,
                "dtype": "survey",
            }
            try:
                resp = requests.get(url, params=params, timeout=20)
                resp.raise_for_status()
                data = resp.json()
                rows = data.get("result", {}).get("rows", []) if isinstance(data, dict) else []
                for row in rows:
                    raw.append({
                        "iso3": iso3,
                        "indicator_code": f"IHSN_{iso3}_{row.get('id', '')}",
                        "year": row.get("year_start") or row.get("year"),
                        "value": 1,
                        "unit": "survey",
                        "title": row.get("title", ""),
                        "survey_id": row.get("id"),
                        "dtype": row.get("dtype", "survey"),
                    })
            except Exception as exc:
                logger.debug("IHSN NADA fetch error for %s: %s", iso3, exc)

        return raw

    def normalise(self, raw: list[dict]) -> list[dict]:
        out = []
        for r in raw:
            if not r.get("year"):
                continue
            out.append({
                "country_iso3": r["iso3"],
                "indicator_code": r["indicator_code"],
                "year": int(r["year"]),
                "value": float(r["value"]),
                "unit": r.get("unit", "survey"),
                "data_source": "IHSN/NADA Survey Catalog",
                "source_id": self.source_id,
                "metadata": {
                    "survey_title": r.get("title", ""),
                    "survey_id": r.get("survey_id"),
                    "dtype": r.get("dtype", "survey"),
                },
            })
        return out


from app.services.connector_service import register_connector
register_connector(IHSNNADAConnector())
