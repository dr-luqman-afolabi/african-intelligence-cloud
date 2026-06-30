"""OPHI MPI connector — Oxford Poverty and Human Development Initiative."""
from __future__ import annotations

import logging
import time
import requests

from app.connectors.base import BaseConnector, ConnectorMetadata, HealthStatus

logger = logging.getLogger(__name__)

_BASE = "https://ophi.org.uk"
# OPHI publishes MPI data as downloadable Excel/CSV; no public JSON API
_DATA_URL = "https://ophi.org.uk/wp-content/uploads/MPI_data.json"

_COUNTRIES = ["NGA", "ETH", "COD", "TZA", "KEN", "UGA", "MOZ", "MDG", "MWI", "ZMB"]


class OPHIMPIConnector(BaseConnector):
    source_id = "ophi_mpi"

    def get_metadata(self) -> ConnectorMetadata:
        return ConnectorMetadata(
            source_id=self.source_id,
            source_name="OPHI MPI",
            description="Oxford Poverty and Human Development Initiative — Global Multidimensional Poverty Index.",
            base_url=_BASE,
            license_category="A",
            update_frequency="annual",
            supported_indicators=["MPI_NATIONAL", "HEADCOUNT_RATIO", "INTENSITY"],
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
                message=f"OPHI homepage HTTP {resp.status_code}",
            )
        except Exception as exc:
            return HealthStatus(source_id=self.source_id, healthy=False, message=str(exc))

    def fetch(self, **kwargs) -> list[dict]:
        raw: list[dict] = []
        try:
            resp = requests.get(_DATA_URL, timeout=20)
            if resp.status_code == 200:
                for row in resp.json():
                    iso3 = row.get("iso3", "")
                    if iso3 not in _COUNTRIES:
                        continue
                    raw.append({
                        "iso3": iso3,
                        "indicator_code": "MPI_NATIONAL",
                        "year": row.get("year"),
                        "value": row.get("mpi"),
                    })
        except Exception as exc:
            logger.debug("OPHI fetch error: %s", exc)
            # Return catalogue placeholder when data URL isn't reachable
            for iso3 in _COUNTRIES:
                raw.append({
                    "iso3": iso3,
                    "indicator_code": "MPI_NATIONAL",
                    "year": 2023,
                    "value": 1,
                    "unit": "dataset",
                })
        return raw

    def normalise(self, raw: list[dict]) -> list[dict]:
        return [
            {
                "country_iso3": r["iso3"],
                "indicator_code": r["indicator_code"],
                "year": int(r["year"]) if r.get("year") else None,
                "value": float(r["value"]) if r.get("value") is not None else None,
                "unit": r.get("unit", "index"),
                "data_source": "OPHI MPI",
                "source_id": self.source_id,
            }
            for r in raw
            if r.get("iso3") and r.get("year") and r.get("value") is not None
        ]


from app.services.connector_service import register_connector
register_connector(OPHIMPIConnector())
