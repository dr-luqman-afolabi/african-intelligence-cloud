"""Polity5 connector — regime characteristics and political authority scores."""
from __future__ import annotations

import logging
import time
import requests

from app.connectors.base import BaseConnector, ConnectorMetadata, HealthStatus

logger = logging.getLogger(__name__)

_BASE = "https://www.systemicpeace.org"
# Polity5 data is distributed as Excel/CSV via the Center for Systemic Peace
_DOWNLOAD_PAGE = "https://www.systemicpeace.org/inscrdata.html"

_COUNTRIES = ["NGA", "ETH", "COD", "ZAF", "KEN", "EGY", "MAR", "GHA", "SEN", "TZA",
              "ZMB", "MOZ", "UGA", "CMR", "CIV", "MLI", "SDN", "SOM"]

_INDICATORS = {
    "polity2": "Polity2 score (-10 to +10, autocracy to democracy)",
    "democ": "Institutionalized democracy score (0-10)",
    "autoc": "Institutionalized autocracy score (0-10)",
    "durable": "Regime durability (years since last regime transition)",
}


class Polity5Connector(BaseConnector):
    source_id = "polity5"

    def get_metadata(self) -> ConnectorMetadata:
        return ConnectorMetadata(
            source_id=self.source_id,
            source_name="Polity5",
            description="Center for Systemic Peace — Polity5 political authority and regime characteristics.",
            base_url=_BASE,
            license_category="A",
            update_frequency="annual",
            supported_indicators=list(_INDICATORS.keys()),
            supported_countries=_COUNTRIES,
        )

    def health_check(self) -> HealthStatus:
        try:
            t0 = time.monotonic()
            resp = requests.get(_BASE, timeout=10)
            latency = round((time.monotonic() - t0) * 1000, 1)
            return HealthStatus(
                source_id=self.source_id,
                healthy=resp.status_code == 200,
                latency_ms=latency,
                message=f"Polity5/CSP homepage HTTP {resp.status_code}",
            )
        except Exception as exc:
            return HealthStatus(source_id=self.source_id, healthy=False, message=str(exc))

    def fetch(self, **kwargs) -> list[dict]:
        # Polity5 requires manual download; return catalogue records
        raw: list[dict] = []
        for iso3 in _COUNTRIES:
            for indicator in _INDICATORS:
                raw.append({
                    "iso3": iso3,
                    "indicator_code": indicator,
                    "year": 2018,
                    "value": 1,
                    "unit": "dataset",
                    "note": f"Download from {_DOWNLOAD_PAGE}",
                })
        return raw

    def normalise(self, raw: list[dict]) -> list[dict]:
        return [
            {
                "country_iso3": r["iso3"],
                "indicator_code": r["indicator_code"],
                "year": r["year"],
                "value": float(r["value"]),
                "unit": r.get("unit", "score"),
                "data_source": "Polity5",
                "source_id": self.source_id,
            }
            for r in raw
            if r.get("iso3") and r.get("year") and r.get("value") is not None
        ]


from app.services.connector_service import register_connector
register_connector(Polity5Connector())
