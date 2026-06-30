"""Our World in Data connector — open development and health indicators."""
from __future__ import annotations

import logging
import time
import requests

from app.connectors.base import BaseConnector, ConnectorMetadata, HealthStatus

logger = logging.getLogger(__name__)

_BASE = "https://ourworldindata.org"
_API_BASE = "https://ourworldindata.org/grapher"
# OWID ETL catalog — metadata for all datasets
_CATALOG_URL = "https://catalog.ourworldindata.org/index.json"

_COUNTRIES = ["NGA", "ETH", "COD", "ZAF", "KEN", "TZA", "UGA", "GHA", "MOZ", "ZMB"]

_INDICATORS = {
    "owid_gdp_per_capita": "GDP per capita (PPP, constant 2017 international $)",
    "owid_life_expectancy": "Life expectancy at birth (years)",
    "owid_child_mortality": "Child mortality rate (under 5, per 1000 births)",
    "owid_access_electricity": "Share of population with access to electricity (%)",
    "owid_co2_per_capita": "CO2 emissions per capita (tonnes)",
}


class OWIDConnector(BaseConnector):
    source_id = "owid"

    def get_metadata(self) -> ConnectorMetadata:
        return ConnectorMetadata(
            source_id=self.source_id,
            source_name="Our World in Data",
            description="Open development indicators from Our World in Data across health, economics, and environment.",
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
                message=f"OWID HTTP {resp.status_code}",
            )
        except Exception as exc:
            return HealthStatus(source_id=self.source_id, healthy=False, message=str(exc))

    def _fetch_indicator(self, indicator: str, chart_slug: str) -> list[dict]:
        """Fetch CSV data from OWID chart download endpoint."""
        url = f"{_API_BASE}/{chart_slug}.csv"
        records = []
        try:
            resp = requests.get(url, timeout=30)
            if resp.status_code != 200:
                return records
            for line in resp.text.splitlines()[1:]:
                parts = line.split(",")
                if len(parts) < 4:
                    continue
                iso3 = parts[1].strip().upper()
                if iso3 not in _COUNTRIES:
                    continue
                try:
                    year = int(parts[2].strip())
                    value = float(parts[3].strip())
                    records.append({"iso3": iso3, "indicator_code": indicator, "year": year, "value": value})
                except (ValueError, IndexError):
                    continue
        except Exception as exc:
            logger.debug("OWID fetch error for %s: %s", indicator, exc)
        return records

    def fetch(self, **kwargs) -> list[dict]:
        raw: list[dict] = []
        chart_slugs = {
            "owid_gdp_per_capita": "gdp-per-capita-worldbank",
            "owid_life_expectancy": "life-expectancy",
            "owid_child_mortality": "child-mortality",
            "owid_access_electricity": "share-of-the-population-with-access-to-electricity",
            "owid_co2_per_capita": "co-emissions-per-capita",
        }
        for indicator, slug in chart_slugs.items():
            raw.extend(self._fetch_indicator(indicator, slug))
        return raw

    def normalise(self, raw: list[dict]) -> list[dict]:
        return [
            {
                "country_iso3": r["iso3"],
                "indicator_code": r["indicator_code"],
                "year": r["year"],
                "value": r["value"],
                "unit": "",
                "data_source": "Our World in Data",
                "source_id": self.source_id,
            }
            for r in raw
            if r.get("iso3") and r.get("year") and r.get("value") is not None
        ]


from app.services.connector_service import register_connector
register_connector(OWIDConnector())
