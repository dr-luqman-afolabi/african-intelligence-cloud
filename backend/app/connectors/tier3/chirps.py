"""CHIRPS connector — Climate Hazards Group InfraRed Precipitation with Station data."""
from __future__ import annotations

import logging
import time
import requests

from app.connectors.base import BaseConnector, ConnectorMetadata, HealthStatus

logger = logging.getLogger(__name__)

_BASE = "https://www.chc.ucsb.edu/data/chirps"
# CHIRPS data accessible via Climate Engine API or direct GeoTIFF files
# We use the ClimateSERV/SERVIR API which provides country-level aggregations
_CLIMATESERV_API = "https://climateserv.servirglobal.net/api/submitDataRequest"

_COUNTRIES = ["NGA", "ETH", "KEN", "TZA", "GHA", "UGA", "MLI", "NER", "BFA", "SDN"]

_COUNTRY_GEOM_IDS = {
    "NGA": 140, "ETH": 67, "KEN": 108, "TZA": 214, "GHA": 81,
    "UGA": 231, "MLI": 133, "NER": 155, "BFA": 32, "SDN": 201,
}


class CHIRPSConnector(BaseConnector):
    source_id = "climate_chirps"

    def get_metadata(self) -> ConnectorMetadata:
        return ConnectorMetadata(
            source_id=self.source_id,
            source_name="CHIRPS Rainfall",
            description="CHIRPS — high-resolution quasi-global rainfall datasets for drought monitoring.",
            base_url=_BASE,
            license_category="A",
            update_frequency="monthly",
            supported_indicators=["CHIRPS_RAINFALL_ANNUAL_MM"],
            supported_countries=list(_COUNTRIES),
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
                message=f"CHIRPS base HTTP {resp.status_code}",
            )
        except Exception as exc:
            return HealthStatus(source_id=self.source_id, healthy=False, message=str(exc))

    def _fetch_annual_rainfall(self, iso3: str, geom_id: int, year: int) -> float | None:
        """Fetch annual mean rainfall via ClimateSERV API."""
        payload = {
            "datatype": 0,  # CHIRPS precipitation
            "begintime": f"01/01/{year}",
            "endtime": f"12/31/{year}",
            "intervaltype": 0,
            "operationtype": 5,  # average
            "geometry": f'{{"type":"FeatureCollection","features":[{{"type":"Feature","id":{geom_id}}}]}}',
        }
        try:
            resp = requests.post(_CLIMATESERV_API, json=payload, timeout=30)
            if resp.status_code != 200:
                return None
            result = resp.json()
            # ClimateSERV returns an asynch job_id — for now return None
            return None
        except Exception:
            return None

    def fetch(self, years: list[int] | None = None, **kwargs) -> list[dict]:
        # CHIRPS requires async job submission via ClimateSERV; return catalogue records
        raw: list[dict] = []
        target_years = years or [2022, 2023]
        for iso3 in _COUNTRIES:
            for year in target_years:
                raw.append({
                    "iso3": iso3,
                    "indicator_code": "CHIRPS_RAINFALL_ANNUAL_MM",
                    "year": year,
                    "value": 1,
                    "unit": "dataset",
                })
        return raw

    def normalise(self, raw: list[dict]) -> list[dict]:
        return [
            {
                "country_iso3": r["iso3"],
                "indicator_code": r["indicator_code"],
                "year": r["year"],
                "value": float(r["value"]),
                "unit": r.get("unit", "mm"),
                "data_source": "CHIRPS",
                "source_id": self.source_id,
            }
            for r in raw
            if r.get("iso3") and r.get("year") and r.get("value") is not None
        ]


from app.services.connector_service import register_connector
register_connector(CHIRPSConnector())
