"""World Bank Microdata Library connector.

Queries the Microdata Catalog API for household surveys, LSMS, and census
datasets hosted by the World Bank for African countries. Returns catalogue-
level metadata; actual microdata files require user registration and approval.
"""
from __future__ import annotations

import logging
import time
import requests

from app.connectors.base import BaseConnector, ConnectorMetadata, HealthStatus

logger = logging.getLogger(__name__)

_CATALOG_BASE = "https://microdata.worldbank.org/index.php/api/catalog"

_COUNTRIES = [
    "NGA", "ETH", "KEN", "GHA", "TZA", "UGA", "RWA", "MOZ", "ZMB",
    "CMR", "SEN", "CIV", "MDG", "NER", "MLI", "BFA", "MWI", "ZWE",
    "ZAF", "SDN", "BGD",  # Bangladesh included as comparative reference
]

# Country name tokens used in WB Microdata keyword search
_COUNTRY_KEYWORDS = {
    "NGA": "Nigeria", "ETH": "Ethiopia", "KEN": "Kenya", "GHA": "Ghana",
    "TZA": "Tanzania", "UGA": "Uganda", "RWA": "Rwanda", "MOZ": "Mozambique",
    "ZMB": "Zambia", "CMR": "Cameroon", "SEN": "Senegal", "CIV": "Ivory Coast",
    "MDG": "Madagascar", "NER": "Niger", "MLI": "Mali", "BFA": "Burkina Faso",
    "MWI": "Malawi", "ZWE": "Zimbabwe", "ZAF": "South Africa", "SDN": "Sudan",
}

_SURVEY_TYPES = ["hhs", "lsms", "dhs", "mics"]


class WBMicrodataConnector(BaseConnector):
    source_id = "wb_microdata"

    def get_metadata(self) -> ConnectorMetadata:
        return ConnectorMetadata(
            source_id=self.source_id,
            source_name="World Bank Microdata Library",
            description=(
                "World Bank Microdata Catalog — household surveys, LSMS, census, "
                "and development datasets for African countries."
            ),
            base_url=_CATALOG_BASE,
            license_category="C",
            update_frequency="continuous",
            supported_countries=_COUNTRIES,
        )

    def health_check(self) -> HealthStatus:
        url = f"{_CATALOG_BASE}/search"
        params = {"keyword": "Africa", "format": "json", "per_page": 1}
        try:
            t0 = time.monotonic()
            resp = requests.get(url, params=params, timeout=10)
            latency = round((time.monotonic() - t0) * 1000, 1)
            resp.raise_for_status()
            total = resp.json().get("result", {}).get("total", 0)
            return HealthStatus(
                source_id=self.source_id,
                healthy=True,
                latency_ms=latency,
                message=f"Catalog OK — {total} total entries",
            )
        except Exception as exc:
            return HealthStatus(source_id=self.source_id, healthy=False, message=str(exc))

    def fetch(self, **kwargs) -> list[dict]:
        """Return catalogue-level survey records for African countries."""
        raw: list[dict] = []
        for iso3, country_name in _COUNTRY_KEYWORDS.items():
            url = f"{_CATALOG_BASE}/search"
            params = {
                "keyword": country_name,
                "format": "json",
                "per_page": 50,
                "country_iso": iso3,
            }
            try:
                resp = requests.get(url, params=params, timeout=20)
                resp.raise_for_status()
                rows = resp.json().get("result", {}).get("rows", [])
                for survey in rows:
                    raw.append({
                        "iso3": iso3,
                        "indicator_code": f"WB_MICRODATA_{survey.get('id', '')}",
                        "year": survey.get("year_start"),
                        "value": 1,
                        "unit": "survey",
                        "survey_title": survey.get("title", ""),
                        "survey_type": survey.get("type", ""),
                        "catalog_id": survey.get("id"),
                    })
            except Exception as exc:
                logger.debug("WB Microdata fetch error for %s: %s", iso3, exc)
        return raw

    def normalise(self, raw: list[dict]) -> list[dict]:
        out = []
        for r in raw:
            if not r.get("iso3") or not r.get("year"):
                continue
            out.append({
                "country_iso3": r["iso3"],
                "indicator_code": r["indicator_code"],
                "year": int(r["year"]),
                "value": float(r["value"]),
                "unit": r.get("unit", "survey"),
                "data_source": "World Bank Microdata Library",
                "source_id": self.source_id,
                "metadata": {
                    "survey_title": r.get("survey_title", ""),
                    "survey_type": r.get("survey_type", ""),
                    "catalog_id": r.get("catalog_id"),
                },
            })
        return out


from app.services.connector_service import register_connector
register_connector(WBMicrodataConnector())
