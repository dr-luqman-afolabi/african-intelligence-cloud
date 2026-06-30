"""Global Carbon Project connector — CO2 and carbon budget data."""
from __future__ import annotations

import logging
import time
import requests

from app.connectors.base import BaseConnector, ConnectorMetadata, HealthStatus

logger = logging.getLogger(__name__)

_BASE = "https://globalcarbonproject.org"
# GCP publishes territorial emissions via Our World in Data / Zenodo
# Use the GCP's official data URL from their annual publication
_DATA_URL = "https://zenodo.org/record/10177738/files/National_Fossil_Carbon_Emissions_2023v1.0.csv"

_COUNTRIES = ["NGA", "ZAF", "EGY", "DZA", "ETH", "AGO", "LBY", "MAR", "TZA", "GHA"]


class GlobalCarbonProjectConnector(BaseConnector):
    source_id = "global_carbon_project"

    def get_metadata(self) -> ConnectorMetadata:
        return ConnectorMetadata(
            source_id=self.source_id,
            source_name="Global Carbon Project",
            description="GCP annual national fossil CO2 emissions from the Global Carbon Budget.",
            base_url=_BASE,
            license_category="A",
            update_frequency="annual",
            supported_indicators=["GCP_FOSSIL_CO2_TOTAL", "GCP_FOSSIL_CO2_PER_CAPITA"],
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
                message=f"GCP homepage HTTP {resp.status_code}",
            )
        except Exception as exc:
            return HealthStatus(source_id=self.source_id, healthy=False, message=str(exc))

    def fetch(self, **kwargs) -> list[dict]:
        raw: list[dict] = []
        try:
            resp = requests.get(_DATA_URL, timeout=60, stream=True)
            if resp.status_code != 200:
                raise RuntimeError(f"HTTP {resp.status_code}")
            lines = resp.text.splitlines()
            if not lines:
                return raw
            header = [h.strip() for h in lines[0].split(",")]
            iso3_col = next((i for i, h in enumerate(header) if h.upper() == "ISO3"), None)
            year_col = next((i for i, h in enumerate(header) if h.upper() == "YEAR"), None)
            total_col = next((i for i, h in enumerate(header) if "TOTAL" in h.upper()), None)
            if iso3_col is None or year_col is None or total_col is None:
                return raw
            for line in lines[1:]:
                parts = line.split(",")
                if len(parts) <= max(iso3_col, year_col, total_col):
                    continue
                iso3 = parts[iso3_col].strip()
                if iso3 not in _COUNTRIES:
                    continue
                try:
                    raw.append({
                        "iso3": iso3,
                        "indicator_code": "GCP_FOSSIL_CO2_TOTAL",
                        "year": int(parts[year_col].strip()),
                        "value": float(parts[total_col].strip()),
                    })
                except ValueError:
                    continue
        except Exception as exc:
            logger.debug("GCP fetch error: %s", exc)
        return raw

    def normalise(self, raw: list[dict]) -> list[dict]:
        return [
            {
                "country_iso3": r["iso3"],
                "indicator_code": r["indicator_code"],
                "year": r["year"],
                "value": float(r["value"]),
                "unit": "MtCO2",
                "data_source": "Global Carbon Project",
                "source_id": self.source_id,
            }
            for r in raw
            if r.get("iso3") and r.get("year") and r.get("value") is not None
        ]


from app.services.connector_service import register_connector
register_connector(GlobalCarbonProjectConnector())
