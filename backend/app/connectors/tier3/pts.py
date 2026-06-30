"""Political Terror Scale connector — human rights and political violence data."""
from __future__ import annotations

import logging
import time
import requests

from app.connectors.base import BaseConnector, ConnectorMetadata, HealthStatus

logger = logging.getLogger(__name__)

_BASE = "https://www.politicalterrorscale.org"
_API_BASE = "https://www.politicalterrorscale.org/api"

_COUNTRIES = ["NGA", "ETH", "COD", "ZAF", "KEN", "EGY", "MAR", "SDN", "SOM", "MLI",
              "BFA", "NER", "MOZ", "CMR", "UGA", "GHA", "SEN", "TZA", "ZMB", "DZA"]

_INDICATORS = {
    "PTS_A": "Political Terror Scale — Amnesty International source",
    "PTS_H": "Political Terror Scale — Human Rights Watch source",
    "PTS_S": "Political Terror Scale — US State Department source",
}


class PTSConnector(BaseConnector):
    source_id = "pts"

    def get_metadata(self) -> ConnectorMetadata:
        return ConnectorMetadata(
            source_id=self.source_id,
            source_name="Political Terror Scale",
            description="PTS — political violence and human rights abuses (1-5 scale) from AI, HRW, and State Dept.",
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
                message=f"PTS homepage HTTP {resp.status_code}",
            )
        except Exception as exc:
            return HealthStatus(source_id=self.source_id, healthy=False, message=str(exc))

    def fetch(self, years: list[int] | None = None, **kwargs) -> list[dict]:
        raw: list[dict] = []
        target_years = years or list(range(2015, 2024))
        for iso3 in _COUNTRIES:
            for year in target_years:
                url = f"{_API_BASE}/data"
                params = {"iso3": iso3, "year": year, "format": "json"}
                try:
                    resp = requests.get(url, params=params, timeout=15)
                    if resp.status_code != 200:
                        continue
                    data = resp.json()
                    for indicator in _INDICATORS:
                        val = data.get(indicator)
                        if val is not None:
                            raw.append({
                                "iso3": iso3,
                                "indicator_code": indicator,
                                "year": year,
                                "value": val,
                            })
                except Exception as exc:
                    logger.debug("PTS fetch error for %s %s: %s", iso3, year, exc)
        return raw

    def normalise(self, raw: list[dict]) -> list[dict]:
        return [
            {
                "country_iso3": r["iso3"],
                "indicator_code": r["indicator_code"],
                "year": r["year"],
                "value": float(r["value"]),
                "unit": "score_1_5",
                "data_source": "Political Terror Scale",
                "source_id": self.source_id,
            }
            for r in raw
            if r.get("iso3") and r.get("year") and r.get("value") is not None
        ]


from app.services.connector_service import register_connector
register_connector(PTSConnector())
