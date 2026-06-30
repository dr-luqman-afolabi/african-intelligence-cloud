"""Afrobarometer connector — public opinion surveys across Africa."""
from __future__ import annotations

import logging
import time
import requests

from app.connectors.base import BaseConnector, ConnectorMetadata, HealthStatus

logger = logging.getLogger(__name__)

_BASE = "https://www.afrobarometer.org"
_API_BASE = "https://api.afrobarometer.org/api/v2"

_COUNTRIES = ["NGA", "ETH", "KEN", "GHA", "TZA", "UGA", "ZAF", "SEN", "CIV", "ZMB",
              "MOZ", "MLI", "BEN", "MWI", "ZWE", "BWA", "NAM", "TGO", "GIN", "SLE"]

_INDICATORS = {
    "AB_DEMOC_PREF": "Democratic preference score",
    "AB_TRUST_GOVT": "Trust in national government",
    "AB_POVERTY": "Experienced food poverty (last year)",
    "AB_CORRUPTION": "Corruption in government",
}


class AfrobarometerConnector(BaseConnector):
    source_id = "afrobarometer_public"

    def get_metadata(self) -> ConnectorMetadata:
        return ConnectorMetadata(
            source_id=self.source_id,
            source_name="Afrobarometer",
            description="Afrobarometer public opinion surveys — democracy, governance, and living conditions.",
            base_url=_BASE,
            license_category="A",
            update_frequency="periodic",
            supported_indicators=list(_INDICATORS.keys()),
            supported_countries=_COUNTRIES,
        )

    def health_check(self) -> HealthStatus:
        url = f"{_API_BASE}/countries"
        try:
            t0 = time.monotonic()
            resp = requests.get(url, timeout=10, headers={"Accept": "application/json"})
            latency = round((time.monotonic() - t0) * 1000, 1)
            if resp.status_code in (200, 401, 403):
                return HealthStatus(
                    source_id=self.source_id,
                    healthy=True,
                    latency_ms=latency,
                    message=f"Afrobarometer API HTTP {resp.status_code}",
                )
        except Exception:
            pass
        try:
            t0 = time.monotonic()
            resp = requests.get(_BASE, timeout=8)
            latency = round((time.monotonic() - t0) * 1000, 1)
            return HealthStatus(
                source_id=self.source_id,
                healthy=resp.status_code == 200,
                latency_ms=latency,
                message=f"Afrobarometer homepage HTTP {resp.status_code}",
            )
        except Exception as exc:
            return HealthStatus(source_id=self.source_id, healthy=False, message=str(exc))

    def fetch(self, **kwargs) -> list[dict]:
        raw: list[dict] = []
        for iso3 in _COUNTRIES:
            url = f"{_API_BASE}/data"
            params = {
                "country_iso": iso3,
                "indicators": ",".join(_INDICATORS.keys()),
                "format": "json",
                "page_size": 100,
            }
            try:
                resp = requests.get(url, params=params, timeout=20, headers={"Accept": "application/json"})
                if resp.status_code != 200:
                    continue
                for item in resp.json().get("results", []):
                    raw.append({
                        "iso3": iso3,
                        "indicator_code": item.get("indicator"),
                        "year": item.get("year"),
                        "value": item.get("value"),
                    })
            except Exception as exc:
                logger.debug("Afrobarometer fetch error for %s: %s", iso3, exc)
        return raw

    def normalise(self, raw: list[dict]) -> list[dict]:
        return [
            {
                "country_iso3": r["iso3"],
                "indicator_code": r["indicator_code"],
                "year": int(r["year"]) if r.get("year") else None,
                "value": float(r["value"]),
                "unit": "percent",
                "data_source": "Afrobarometer",
                "source_id": self.source_id,
            }
            for r in raw
            if r.get("iso3") and r.get("year") and r.get("value") is not None
        ]


from app.services.connector_service import register_connector
register_connector(AfrobarometerConnector())
