"""AidData connector — development finance and aid flows data."""
from __future__ import annotations

import logging
import time
import requests

from app.connectors.base import BaseConnector, ConnectorMetadata, HealthStatus

logger = logging.getLogger(__name__)

_BASE = "https://www.aiddata.org"
_API_BASE = "https://api.aiddata.org/api/v1"

_COUNTRIES = ["NGA", "ETH", "KEN", "GHA", "TZA", "UGA", "ZAF", "MOZ", "ZMB", "MLI",
              "SEN", "RWA", "BDI", "MWI", "ZWE", "CMR", "TCD", "COD", "AGO", "SDN"]

_INDICATORS = {
    "AIDDATA_COMMITMENTS_USD": "Total aid commitments (current USD)",
    "AIDDATA_DISBURSEMENTS_USD": "Total aid disbursements (current USD)",
    "AIDDATA_ODA_TOTAL": "ODA flows total",
}


class AidDataConnector(BaseConnector):
    source_id = "aiddata"

    def get_metadata(self) -> ConnectorMetadata:
        return ConnectorMetadata(
            source_id=self.source_id,
            source_name="AidData",
            description="AidData — geocoded development finance and aid flow datasets from bilateral and multilateral donors.",
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
                message=f"AidData homepage HTTP {resp.status_code}",
            )
        except Exception as exc:
            return HealthStatus(source_id=self.source_id, healthy=False, message=str(exc))

    def fetch(self, years: list[int] | None = None, **kwargs) -> list[dict]:
        raw: list[dict] = []
        target_years = years or list(range(2010, 2022))
        for iso3 in _COUNTRIES:
            for year in target_years:
                url = f"{_API_BASE}/transactions"
                params = {
                    "recipient_iso3": iso3,
                    "year": year,
                    "format": "json",
                    "page_size": 1,
                    "aggregate": "true",
                }
                try:
                    resp = requests.get(url, params=params, timeout=20)
                    if resp.status_code != 200:
                        continue
                    data = resp.json()
                    total = data.get("total_commitments") or data.get("total")
                    if total is not None:
                        raw.append({
                            "iso3": iso3,
                            "indicator_code": "AIDDATA_COMMITMENTS_USD",
                            "year": year,
                            "value": float(total),
                        })
                except Exception as exc:
                    logger.debug("AidData fetch error for %s %s: %s", iso3, year, exc)
        return raw

    def normalise(self, raw: list[dict]) -> list[dict]:
        return [
            {
                "country_iso3": r["iso3"],
                "indicator_code": r["indicator_code"],
                "year": r["year"],
                "value": float(r["value"]),
                "unit": "USD",
                "data_source": "AidData",
                "source_id": self.source_id,
            }
            for r in raw
            if r.get("iso3") and r.get("year") and r.get("value") is not None
        ]


from app.services.connector_service import register_connector
register_connector(AidDataConnector())
