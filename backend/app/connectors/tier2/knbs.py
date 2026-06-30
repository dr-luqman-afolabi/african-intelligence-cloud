"""KNBS connector — Kenya National Bureau of Statistics."""
from __future__ import annotations

import logging
import time
import requests

from app.connectors.base import BaseConnector, ConnectorMetadata, HealthStatus

logger = logging.getLogger(__name__)

_BASE = "https://www.knbs.or.ke"
_OPENDATA_BASE = "https://opendata.knbs.or.ke/api"

_ISO3 = "KEN"

# Key KNBS indicators available via their API or publications
_INDICATORS = {
    "KNBS_GDP_GROWTH": "GDP growth rate",
    "KNBS_CPI_INFLATION": "Consumer Price Index — inflation",
    "KNBS_UNEMPLOYMENT": "Unemployment rate",
    "KNBS_POVERTY_HEADCOUNT": "Poverty headcount ratio",
}


class KNBSConnector(BaseConnector):
    source_id = "knbs"

    def get_metadata(self) -> ConnectorMetadata:
        return ConnectorMetadata(
            source_id=self.source_id,
            source_name="Kenya National Bureau of Statistics",
            description="KNBS official Kenya economic and social statistics.",
            base_url=_BASE,
            license_category="B",
            update_frequency="annual",
            supported_indicators=list(_INDICATORS.keys()),
            supported_countries=[_ISO3],
        )

    def health_check(self) -> HealthStatus:
        url = f"{_OPENDATA_BASE}/3/action/package_search"
        params = {"q": "GDP", "rows": 1}
        try:
            t0 = time.monotonic()
            resp = requests.get(url, params=params, timeout=10)
            latency = round((time.monotonic() - t0) * 1000, 1)
            if resp.status_code == 200:
                return HealthStatus(source_id=self.source_id, healthy=True, latency_ms=latency, message="OpenData OK")
        except Exception:
            pass
        try:
            t0 = time.monotonic()
            resp = requests.get(_BASE, timeout=8)
            latency = round((time.monotonic() - t0) * 1000, 1)
            return HealthStatus(
                source_id=self.source_id,
                healthy=resp.status_code == 200,
                latency_ms=latency,
                message=f"KNBS homepage HTTP {resp.status_code}",
            )
        except Exception as exc:
            return HealthStatus(source_id=self.source_id, healthy=False, message=str(exc))

    def fetch(self, **kwargs) -> list[dict]:
        """Catalogue records from KNBS OpenData; structured data requires bilateral access."""
        raw: list[dict] = []
        url = f"{_OPENDATA_BASE}/3/action/package_search"
        params = {"rows": 50, "sort": "metadata_modified desc"}
        try:
            resp = requests.get(url, params=params, timeout=20)
            if resp.status_code == 200:
                for pkg in resp.json().get("result", {}).get("results", []):
                    raw.append({
                        "iso3": _ISO3,
                        "indicator_code": f"KNBS_{pkg.get('id', '')[:12]}",
                        "year": int(pkg.get("metadata_created", "2020")[:4]),
                        "value": 1,
                        "unit": "dataset",
                    })
        except Exception as exc:
            logger.debug("KNBS fetch error: %s", exc)
        return raw

    def normalise(self, raw: list[dict]) -> list[dict]:
        return [
            {
                "country_iso3": r["iso3"],
                "indicator_code": r["indicator_code"],
                "year": r["year"],
                "value": float(r["value"]),
                "unit": r.get("unit", ""),
                "data_source": "Kenya National Bureau of Statistics",
                "source_id": self.source_id,
            }
            for r in raw
            if r.get("year")
        ]


from app.services.connector_service import register_connector
register_connector(KNBSConnector())
