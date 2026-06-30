"""Climate Watch connector — GHG emissions and NDC data."""
from __future__ import annotations

import logging
import time
import requests

from app.connectors.base import BaseConnector, ConnectorMetadata, HealthStatus

logger = logging.getLogger(__name__)

_BASE = "https://www.climatewatchdata.org/api/v1"

_COUNTRIES = ["NGA", "ETH", "COD", "ZAF", "KEN", "EGY", "MAR", "DZA", "AGO", "TZA"]

_INDICATORS = {
    "total_including_lucf": "Total GHG emissions including LUCF (MtCO2e)",
    "total_excluding_lucf": "Total GHG emissions excluding LUCF (MtCO2e)",
}


class ClimateWatchConnector(BaseConnector):
    source_id = "climate_watch"

    def get_metadata(self) -> ConnectorMetadata:
        return ConnectorMetadata(
            source_id=self.source_id,
            source_name="Climate Watch",
            description="Climate Watch — GHG emissions, NDC targets, and climate finance data.",
            base_url="https://www.climatewatchdata.org",
            license_category="A",
            update_frequency="annual",
            supported_indicators=list(_INDICATORS.keys()),
            supported_countries=_COUNTRIES,
        )

    def health_check(self) -> HealthStatus:
        url = f"{_BASE}/emissions"
        params = {"source": "CAIT", "countries[]": "NGA", "start_year": 2018, "end_year": 2020}
        try:
            t0 = time.monotonic()
            resp = requests.get(url, params=params, timeout=10)
            latency = round((time.monotonic() - t0) * 1000, 1)
            return HealthStatus(
                source_id=self.source_id,
                healthy=resp.status_code == 200,
                latency_ms=latency,
                message=f"Climate Watch API HTTP {resp.status_code}",
            )
        except Exception as exc:
            return HealthStatus(source_id=self.source_id, healthy=False, message=str(exc))

    def fetch(self, years: list[int] | None = None, **kwargs) -> list[dict]:
        raw: list[dict] = []
        start_year = min(years) if years else 2010
        end_year = max(years) if years else 2022
        for iso3 in _COUNTRIES:
            url = f"{_BASE}/emissions"
            params = {
                "source": "CAIT",
                "countries[]": iso3,
                "start_year": start_year,
                "end_year": end_year,
            }
            try:
                resp = requests.get(url, params=params, timeout=20)
                if resp.status_code != 200:
                    continue
                for item in resp.json().get("data", []):
                    for emission in item.get("emissions", []):
                        sector = emission.get("sector", "")
                        if "Total" not in sector:
                            continue
                        include_lucf = "LUCF" in sector
                        code = "total_including_lucf" if include_lucf else "total_excluding_lucf"
                        for yr, val in zip(emission.get("years", []), emission.get("values", [])):
                            if val is not None:
                                raw.append({
                                    "iso3": iso3,
                                    "indicator_code": code,
                                    "year": yr,
                                    "value": val,
                                })
            except Exception as exc:
                logger.debug("Climate Watch fetch error for %s: %s", iso3, exc)
        return raw

    def normalise(self, raw: list[dict]) -> list[dict]:
        return [
            {
                "country_iso3": r["iso3"],
                "indicator_code": r["indicator_code"],
                "year": r["year"],
                "value": float(r["value"]),
                "unit": "MtCO2e",
                "data_source": "Climate Watch",
                "source_id": self.source_id,
            }
            for r in raw
            if r.get("iso3") and r.get("year") and r.get("value") is not None
        ]


from app.services.connector_service import register_connector
register_connector(ClimateWatchConnector())
