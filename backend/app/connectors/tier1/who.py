"""WHO Global Health Observatory connector."""
from __future__ import annotations

import logging
import time
import requests

from app.connectors.base import BaseConnector, ConnectorMetadata, HealthStatus

logger = logging.getLogger(__name__)

_BASE = "https://ghoapi.azureedge.net/api"

_INDICATORS = {
    "WHOSIS_000001": "Life expectancy at birth (years)",
    "MDG_0000000001": "Under-5 mortality rate",
    "NUTRITION_ANT_WHZ_NE2": "Wasting prevalence (% under 5)",
    "MALARIA_DEATHS_P100000": "Malaria deaths per 100 000",
    "SDGPM25": "Mean PM2.5 concentration",
}

_COUNTRIES = [
    "NGA", "ZAF", "KEN", "ETH", "GHA", "TZA", "UGA", "RWA",
    "MOZ", "ZMB", "CMR", "SEN", "CIV", "MDG", "NER", "MLI", "BFA", "SDN",
]


class WHOConnector(BaseConnector):
    source_id = "who"

    def get_metadata(self) -> ConnectorMetadata:
        return ConnectorMetadata(
            source_id=self.source_id,
            source_name="WHO Global Health Observatory",
            description="WHO GHO health indicators for African countries.",
            base_url=_BASE,
            license_category="A",
            update_frequency="annual",
            supported_indicators=list(_INDICATORS.keys()),
            supported_countries=_COUNTRIES,
        )

    def health_check(self) -> HealthStatus:
        url = f"{_BASE}/WHOSIS_000001?$top=1"
        try:
            t0 = time.monotonic()
            resp = requests.get(url, timeout=10, headers={"Accept": "application/json"})
            latency = round((time.monotonic() - t0) * 1000, 1)
            resp.raise_for_status()
            return HealthStatus(source_id=self.source_id, healthy=True, latency_ms=latency, message="OK")
        except Exception as exc:
            return HealthStatus(source_id=self.source_id, healthy=False, message=str(exc))

    def fetch(self, **kwargs) -> list[dict]:
        raw: list[dict] = []
        country_filter = " or ".join(f"SpatialDim eq '{c}'" for c in _COUNTRIES)
        for code in _INDICATORS:
            url = f"{_BASE}/{code}"
            params = {"$filter": country_filter, "$select": "SpatialDim,TimeDim,NumericValue"}
            try:
                resp = requests.get(url, params=params, timeout=30, headers={"Accept": "application/json"})
                resp.raise_for_status()
                for row in resp.json().get("value", []):
                    if row.get("NumericValue") is not None:
                        raw.append({
                            "iso3": row.get("SpatialDim", ""),
                            "indicator_code": code,
                            "year": row.get("TimeDim"),
                            "value": row.get("NumericValue"),
                        })
            except Exception as exc:
                logger.warning("WHO fetch error for %s: %s", code, exc)
        return raw

    def normalise(self, raw: list[dict]) -> list[dict]:
        return [
            {
                "country_iso3": r["iso3"],
                "indicator_code": r["indicator_code"],
                "year": int(r["year"]) if r.get("year") else None,
                "value": float(r["value"]),
                "unit": "",
                "data_source": "WHO Global Health Observatory",
                "source_id": self.source_id,
            }
            for r in raw
            if r.get("iso3") and r.get("year") and r.get("value") is not None
        ]


from app.services.connector_service import register_connector
register_connector(WHOConnector())
