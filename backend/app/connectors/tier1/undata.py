"""UN SDG Indicators API connector."""
from __future__ import annotations

import logging
import time
import requests

from app.connectors.base import BaseConnector, ConnectorError, ConnectorMetadata, HealthStatus

logger = logging.getLogger(__name__)

_BASE = "https://unstats.un.org/sdgapi/v1/sdg"

_GOALS = ["1", "2", "3", "4", "8", "10"]  # Core SDGs for Africa

_COUNTRIES = [
    "NGA", "ZAF", "KEN", "ETH", "GHA", "TZA", "UGA", "RWA",
    "MOZ", "ZMB", "CMR", "SEN", "CIV", "MDG", "NER",
]


class UNDataConnector(BaseConnector):
    source_id = "un_sdg"

    def get_metadata(self) -> ConnectorMetadata:
        return ConnectorMetadata(
            source_id=self.source_id,
            source_name="UN SDG Indicators",
            description="UN Sustainable Development Goals indicators via unstats.un.org API.",
            base_url=_BASE,
            license_category="A",
            update_frequency="annual",
            supported_indicators=[f"SDG_GOAL_{g}" for g in _GOALS],
            supported_countries=_COUNTRIES,
        )

    def health_check(self) -> HealthStatus:
        url = f"{_BASE}/Goal/1/Target/List"
        try:
            t0 = time.monotonic()
            resp = requests.get(url, timeout=10)
            latency = round((time.monotonic() - t0) * 1000, 1)
            resp.raise_for_status()
            return HealthStatus(source_id=self.source_id, healthy=True, latency_ms=latency, message="OK")
        except Exception as exc:
            return HealthStatus(source_id=self.source_id, healthy=False, message=str(exc))

    def fetch(self, **kwargs) -> list[dict]:
        raw: list[dict] = []
        for goal in _GOALS:
            url = f"{_BASE}/Goal/{goal}/GeoArea/Data/Current"
            params = {"areaCode": ",".join(_COUNTRIES), "pageSize": 500}
            try:
                resp = requests.get(url, params=params, timeout=30)
                resp.raise_for_status()
                items = resp.json().get("data", [])
                for item in items:
                    for series in item.get("series", []):
                        for obs in series.get("observations", []):
                            raw.append({
                                "iso3": item.get("geoAreaCode", ""),
                                "indicator_code": series.get("seriesCode", f"SDG_GOAL_{goal}"),
                                "indicator_name": series.get("seriesDescription", ""),
                                "year": int(obs[0]) if obs else None,
                                "value": obs[1] if len(obs) > 1 else None,
                                "unit": series.get("units", ""),
                            })
            except Exception as exc:
                logger.warning("UNData fetch error for goal %s: %s", goal, exc)
        return raw

    def normalise(self, raw: list[dict]) -> list[dict]:
        return [
            {
                "country_iso3": r["iso3"],
                "indicator_code": r["indicator_code"],
                "year": r["year"],
                "value": r["value"],
                "unit": r.get("unit", ""),
                "data_source": "UN SDG Indicators",
                "source_id": self.source_id,
            }
            for r in raw
            if r.get("iso3") and r.get("year") is not None and r.get("value") is not None
        ]


from app.services.connector_service import register_connector
register_connector(UNDataConnector())
