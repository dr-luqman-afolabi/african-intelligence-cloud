"""ACLED connector — Armed Conflict Location and Event Data."""
from __future__ import annotations

import logging
import time
import requests

from app.config import get_settings
from app.connectors.base import BaseConnector, ConnectorMetadata, HealthStatus

logger = logging.getLogger(__name__)

_BASE = "https://api.acleddata.com"

_COUNTRIES = ["Nigeria", "Ethiopia", "DRC", "Sudan", "Somalia", "South Sudan",
              "Mali", "Burkina Faso", "Niger", "Mozambique", "CAR", "Cameroon",
              "South Africa", "Kenya", "Uganda", "Ghana", "Tanzania"]

_ISO3_MAP = {
    "Nigeria": "NGA", "Ethiopia": "ETH", "DRC": "COD", "Sudan": "SDN",
    "Somalia": "SOM", "South Sudan": "SSD", "Mali": "MLI",
    "Burkina Faso": "BFA", "Niger": "NER", "Mozambique": "MOZ",
    "CAR": "CAF", "Cameroon": "CMR", "South Africa": "ZAF",
    "Kenya": "KEN", "Uganda": "UGA", "Ghana": "GHA", "Tanzania": "TZA",
}


class ACLEDConnector(BaseConnector):
    source_id = "acled"

    def get_metadata(self) -> ConnectorMetadata:
        return ConnectorMetadata(
            source_id=self.source_id,
            source_name="ACLED",
            description="Armed Conflict Location and Event Data — conflict events, fatalities, and protest data.",
            base_url=_BASE,
            license_category="B",
            update_frequency="weekly",
            supported_indicators=["ACLED_EVENTS", "ACLED_FATALITIES", "ACLED_PROTESTS"],
            supported_countries=list(_ISO3_MAP.values()),
        )

    def health_check(self) -> HealthStatus:
        settings = get_settings()
        api_key = getattr(settings, "acled_api_key", None)
        email = getattr(settings, "acled_email", None)
        if not (api_key and email):
            return HealthStatus(
                source_id=self.source_id,
                healthy=False,
                message="ACLED requires acled_api_key + acled_email settings",
            )
        url = f"{_BASE}/acled/read"
        params = {"key": api_key, "email": email, "country": "Nigeria", "year": 2023, "limit": 1}
        try:
            t0 = time.monotonic()
            resp = requests.get(url, params=params, timeout=10)
            latency = round((time.monotonic() - t0) * 1000, 1)
            return HealthStatus(
                source_id=self.source_id,
                healthy=resp.status_code == 200,
                latency_ms=latency,
                message=f"ACLED API HTTP {resp.status_code}",
            )
        except Exception as exc:
            return HealthStatus(source_id=self.source_id, healthy=False, message=str(exc))

    def fetch(self, years: list[int] | None = None, **kwargs) -> list[dict]:
        settings = get_settings()
        api_key = getattr(settings, "acled_api_key", None)
        email = getattr(settings, "acled_email", None)
        if not (api_key and email):
            logger.warning("ACLED: missing acled_api_key or acled_email — skipping fetch")
            return []

        target_years = years or [2022, 2023]
        raw: list[dict] = []
        for country in _COUNTRIES:
            for year in target_years:
                url = f"{_BASE}/acled/read"
                params = {
                    "key": api_key,
                    "email": email,
                    "country": country,
                    "year": year,
                    "fields": "iso3|year|event_type|fatalities",
                    "limit": 5000,
                }
                try:
                    resp = requests.get(url, params=params, timeout=30)
                    if resp.status_code != 200:
                        continue
                    events = resp.json().get("data", [])
                    total_events = len(events)
                    total_fatalities = sum(int(e.get("fatalities", 0) or 0) for e in events)
                    iso3 = _ISO3_MAP.get(country, "")
                    if iso3 and total_events:
                        raw.append({
                            "iso3": iso3, "indicator_code": "ACLED_EVENTS",
                            "year": year, "value": total_events,
                        })
                        raw.append({
                            "iso3": iso3, "indicator_code": "ACLED_FATALITIES",
                            "year": year, "value": total_fatalities,
                        })
                except Exception as exc:
                    logger.warning("ACLED fetch error for %s %s: %s", country, year, exc)
        return raw

    def normalise(self, raw: list[dict]) -> list[dict]:
        return [
            {
                "country_iso3": r["iso3"],
                "indicator_code": r["indicator_code"],
                "year": r["year"],
                "value": float(r["value"]),
                "unit": "count",
                "data_source": "ACLED",
                "source_id": self.source_id,
            }
            for r in raw
            if r.get("iso3") and r.get("year") and r.get("value") is not None
        ]


from app.services.connector_service import register_connector
register_connector(ACLEDConnector())
