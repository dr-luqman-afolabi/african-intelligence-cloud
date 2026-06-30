"""V-Dem connector — Varieties of Democracy dataset."""
from __future__ import annotations

import logging
import time
import requests

from app.connectors.base import BaseConnector, ConnectorMetadata, HealthStatus

logger = logging.getLogger(__name__)

_BASE = "https://v-dem.net"
# V-Dem provides data via their API (limited) and bulk Zenodo downloads
_API_BASE = "https://api.vdemdata.com/v1"

_COUNTRIES = ["NGA", "ETH", "KEN", "GHA", "TZA", "UGA", "ZAF", "SEN", "CIV", "ZMB"]

_INDICATORS = {
    "v2x_libdem": "Liberal democracy index",
    "v2x_polyarchy": "Electoral democracy index",
    "v2x_corr": "Political corruption index",
    "v2x_rule": "Rule of law index",
    "v2xcl_disc": "Freedom of discussion index",
}


class VDemConnector(BaseConnector):
    source_id = "vdem"

    def get_metadata(self) -> ConnectorMetadata:
        return ConnectorMetadata(
            source_id=self.source_id,
            source_name="V-Dem",
            description="Varieties of Democracy — democracy, governance, and civil liberties indices.",
            base_url=_BASE,
            license_category="A",
            update_frequency="annual",
            supported_indicators=list(_INDICATORS.keys()),
            supported_countries=_COUNTRIES,
        )

    def health_check(self) -> HealthStatus:
        url = f"{_API_BASE}/data"
        params = {"country_iso": "NGA", "variable": "v2x_libdem", "start_year": 2020, "end_year": 2020}
        try:
            t0 = time.monotonic()
            resp = requests.get(url, params=params, timeout=10)
            latency = round((time.monotonic() - t0) * 1000, 1)
            if resp.status_code in (200, 404):
                return HealthStatus(source_id=self.source_id, healthy=True, latency_ms=latency, message=f"V-Dem API HTTP {resp.status_code}")
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
                message=f"V-Dem homepage HTTP {resp.status_code}",
            )
        except Exception as exc:
            return HealthStatus(source_id=self.source_id, healthy=False, message=str(exc))

    def fetch(self, years: list[int] | None = None, **kwargs) -> list[dict]:
        raw: list[dict] = []
        start_year = min(years) if years else 2000
        end_year = max(years) if years else 2023
        for iso3 in _COUNTRIES:
            for var in _INDICATORS:
                url = f"{_API_BASE}/data"
                params = {
                    "country_iso": iso3,
                    "variable": var,
                    "start_year": start_year,
                    "end_year": end_year,
                }
                try:
                    resp = requests.get(url, params=params, timeout=20)
                    if resp.status_code != 200:
                        continue
                    for row in resp.json().get("data", []):
                        val = row.get(var)
                        if val is not None:
                            raw.append({
                                "iso3": iso3,
                                "indicator_code": var,
                                "year": row.get("year"),
                                "value": val,
                            })
                except Exception as exc:
                    logger.debug("V-Dem fetch error for %s/%s: %s", iso3, var, exc)
        return raw

    def normalise(self, raw: list[dict]) -> list[dict]:
        return [
            {
                "country_iso3": r["iso3"],
                "indicator_code": r["indicator_code"],
                "year": int(r["year"]) if r.get("year") else None,
                "value": float(r["value"]),
                "unit": "index",
                "data_source": "V-Dem",
                "source_id": self.source_id,
            }
            for r in raw
            if r.get("iso3") and r.get("year") and r.get("value") is not None
        ]


from app.services.connector_service import register_connector
register_connector(VDemConnector())
