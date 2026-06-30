"""UN Comtrade connector — international trade statistics."""
from __future__ import annotations

import logging
import time
import requests

from app.connectors.base import BaseConnector, ConnectorMetadata, HealthStatus

logger = logging.getLogger(__name__)

_BASE = "https://comtradeapi.un.org/public/v1/preview"

_COUNTRIES = {
    "NGA": "566", "ZAF": "710", "KEN": "404", "ETH": "231",
    "GHA": "288", "TZA": "834", "UGA": "800", "CIV": "384",
    "CMR": "120", "SEN": "686",
}


class UNComtradeConnector(BaseConnector):
    source_id = "un_comtrade"

    def get_metadata(self) -> ConnectorMetadata:
        return ConnectorMetadata(
            source_id=self.source_id,
            source_name="UN Comtrade",
            description="UN Comtrade international merchandise trade statistics.",
            base_url=_BASE,
            license_category="A",
            update_frequency="annual",
            supported_countries=list(_COUNTRIES.keys()),
        )

    def health_check(self) -> HealthStatus:
        url = f"{_BASE}/C/A/HS/566/TOTAL"
        params = {"reportercode": "566", "period": "2022", "cmdCode": "TOTAL", "flowCode": "X"}
        try:
            t0 = time.monotonic()
            resp = requests.get(url, params=params, timeout=10)
            latency = round((time.monotonic() - t0) * 1000, 1)
            # 200 or 204 are both OK; Comtrade returns 204 for empty results
            healthy = resp.status_code in (200, 204)
            return HealthStatus(source_id=self.source_id, healthy=healthy, latency_ms=latency, message=f"HTTP {resp.status_code}")
        except Exception as exc:
            return HealthStatus(source_id=self.source_id, healthy=False, message=str(exc))

    def fetch(self, years: list[int] | None = None, **kwargs) -> list[dict]:
        raw: list[dict] = []
        target_years = years or [2022, 2021, 2020]
        for iso3, code in _COUNTRIES.items():
            for year in target_years:
                url = f"{_BASE}/C/A/HS/{code}/TOTAL"
                params = {
                    "reportercode": code,
                    "period": str(year),
                    "cmdCode": "TOTAL",
                    "flowCode": "X,M",
                }
                try:
                    resp = requests.get(url, params=params, timeout=20)
                    if resp.status_code == 204:
                        continue
                    resp.raise_for_status()
                    for row in resp.json().get("data", []):
                        raw.append({
                            "iso3": iso3,
                            "indicator_code": f"TRADE_{row.get('flowCode', 'X')}",
                            "year": year,
                            "value": row.get("primaryValue"),
                            "unit": "USD",
                        })
                except Exception as exc:
                    logger.debug("Comtrade fetch error %s/%s: %s", iso3, year, exc)
        return raw

    def normalise(self, raw: list[dict]) -> list[dict]:
        return [
            {
                "country_iso3": r["iso3"],
                "indicator_code": r["indicator_code"],
                "year": r["year"],
                "value": float(r["value"]) if r.get("value") is not None else None,
                "unit": r.get("unit", "USD"),
                "data_source": "UN Comtrade",
                "source_id": self.source_id,
            }
            for r in raw
            if r.get("value") is not None
        ]


from app.services.connector_service import register_connector
register_connector(UNComtradeConnector())
