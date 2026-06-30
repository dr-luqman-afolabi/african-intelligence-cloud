"""ERA5 connector — ECMWF Reanalysis v5 climate data."""
from __future__ import annotations

import logging
import time
import requests

from app.connectors.base import BaseConnector, ConnectorMetadata, HealthStatus

logger = logging.getLogger(__name__)

_BASE = "https://cds.climate.copernicus.eu"
# ERA5 data is available via the Copernicus CDS API (requires API key)
# We use the CDS public info endpoint for health checks
_CDS_INFO = "https://cds.climate.copernicus.eu/api/v2"

_COUNTRIES = ["NGA", "ETH", "KEN", "ZAF", "EGY", "TZA", "GHA", "MAR", "DZA", "AGO"]

_INDICATORS = {
    "ERA5_T2M_ANNUAL_MEAN": "ERA5 annual mean 2m temperature (°C)",
    "ERA5_TP_ANNUAL_TOTAL": "ERA5 annual total precipitation (m)",
    "ERA5_U10_ANNUAL_MEAN": "ERA5 annual mean 10m u-component wind (m/s)",
}


class ERA5Connector(BaseConnector):
    source_id = "era5"

    def get_metadata(self) -> ConnectorMetadata:
        return ConnectorMetadata(
            source_id=self.source_id,
            source_name="ERA5",
            description="ECMWF ERA5 reanalysis — hourly/monthly atmospheric, land, and oceanic climate variables.",
            base_url=_BASE,
            license_category="A",
            update_frequency="monthly",
            supported_indicators=list(_INDICATORS.keys()),
            supported_countries=_COUNTRIES,
        )

    def health_check(self) -> HealthStatus:
        try:
            t0 = time.monotonic()
            resp = requests.get(_CDS_INFO, timeout=10)
            latency = round((time.monotonic() - t0) * 1000, 1)
            return HealthStatus(
                source_id=self.source_id,
                healthy=resp.status_code in (200, 401),
                latency_ms=latency,
                message=f"CDS API HTTP {resp.status_code}",
            )
        except Exception as exc:
            return HealthStatus(source_id=self.source_id, healthy=False, message=str(exc))

    def fetch(self, **kwargs) -> list[dict]:
        # ERA5 requires cdsapi Python client + API key; return catalogue records
        raw: list[dict] = []
        for iso3 in _COUNTRIES:
            for indicator in _INDICATORS:
                raw.append({
                    "iso3": iso3,
                    "indicator_code": indicator,
                    "year": 2022,
                    "value": 1,
                    "unit": "dataset",
                })
        return raw

    def normalise(self, raw: list[dict]) -> list[dict]:
        units = {
            "ERA5_T2M_ANNUAL_MEAN": "°C",
            "ERA5_TP_ANNUAL_TOTAL": "m",
            "ERA5_U10_ANNUAL_MEAN": "m/s",
        }
        return [
            {
                "country_iso3": r["iso3"],
                "indicator_code": r["indicator_code"],
                "year": r["year"],
                "value": float(r["value"]),
                "unit": r.get("unit") or units.get(r["indicator_code"], ""),
                "data_source": "ERA5",
                "source_id": self.source_id,
            }
            for r in raw
            if r.get("iso3") and r.get("year") and r.get("value") is not None
        ]


from app.services.connector_service import register_connector
register_connector(ERA5Connector())
