"""WTO connector — world trade organization statistics."""
from __future__ import annotations

import logging
import time
import requests

from app.connectors.base import BaseConnector, ConnectorMetadata, HealthStatus

logger = logging.getLogger(__name__)

_BASE = "https://api.wto.org/timeseries/v1"

_INDICATORS = {
    "ITS_MTV_AX": "Merchandise trade value, exports (USD)",
    "ITS_MTV_AM": "Merchandise trade value, imports (USD)",
    "ITS_CS_AX5": "Commercial services exports (USD)",
    "ITS_CS_AM5": "Commercial services imports (USD)",
    "HS_M_0010": "Tariff — bound rate",
}

_COUNTRIES = [
    "NGA", "ZAF", "KEN", "ETH", "GHA", "TZA", "UGA", "RWA",
    "MOZ", "SEN", "CMR", "CIV", "ZMB", "NER", "MLI",
]


class WTOConnector(BaseConnector):
    source_id = "wto"

    def get_metadata(self) -> ConnectorMetadata:
        return ConnectorMetadata(
            source_id=self.source_id,
            source_name="WTO Statistics",
            description="World Trade Organization trade statistics for African countries.",
            base_url=_BASE,
            license_category="A",
            update_frequency="annual",
            supported_indicators=list(_INDICATORS.keys()),
            supported_countries=_COUNTRIES,
        )

    def health_check(self) -> HealthStatus:
        url = f"{_BASE}/indicators"
        params = {"lang": 1}
        try:
            t0 = time.monotonic()
            resp = requests.get(url, params=params, timeout=10)
            latency = round((time.monotonic() - t0) * 1000, 1)
            resp.raise_for_status()
            return HealthStatus(source_id=self.source_id, healthy=True, latency_ms=latency, message="OK")
        except Exception as exc:
            return HealthStatus(source_id=self.source_id, healthy=False, message=str(exc))

    def fetch(self, years: list[int] | None = None, **kwargs) -> list[dict]:
        raw: list[dict] = []
        target_years = years or list(range(2015, 2024))
        year_list = ",".join(str(y) for y in target_years)
        country_list = ",".join(_COUNTRIES)
        for indicator_code in _INDICATORS:
            url = f"{_BASE}/data"
            params = {
                "indicator_code": indicator_code,
                "reporting_economy": country_list,
                "period": year_list,
                "output_format": "json",
                "lang": 1,
            }
            try:
                resp = requests.get(url, params=params, timeout=40)
                if resp.status_code == 404:
                    continue
                resp.raise_for_status()
                for row in resp.json().get("Dataset", []):
                    raw.append({
                        "iso3": row.get("reportingEconomyIso3A"),
                        "indicator_code": indicator_code,
                        "year": row.get("Year"),
                        "value": row.get("Value"),
                        "unit": row.get("unitCode", ""),
                    })
            except Exception as exc:
                logger.warning("WTO fetch error for %s: %s", indicator_code, exc)
        return raw

    def normalise(self, raw: list[dict]) -> list[dict]:
        return [
            {
                "country_iso3": r["iso3"],
                "indicator_code": r["indicator_code"],
                "year": int(r["year"]) if r.get("year") else None,
                "value": float(r["value"]) if r.get("value") is not None else None,
                "unit": r.get("unit", ""),
                "data_source": "WTO Statistics",
                "source_id": self.source_id,
            }
            for r in raw
            if r.get("iso3") and r.get("value") is not None
        ]


from app.services.connector_service import register_connector
register_connector(WTOConnector())
