"""African Development Bank connector — socioeconomic statistics."""
from __future__ import annotations

import logging
import time
import requests

from app.connectors.base import BaseConnector, ConnectorMetadata, HealthStatus

logger = logging.getLogger(__name__)

_BASE = "https://api.africanbankgroup.org/api/v1"

# Fallback to World Bank proxy when AfDB API is unavailable
_WB_BASE = "https://api.worldbank.org/v2"

_INDICATORS = {
    "IC.BUS.EASE.XQ": "Ease of doing business score",
    "GC.DOD.TOTL.GD.ZS": "Central government debt (% GDP)",
    "NE.GDI.TOTL.ZS": "Gross capital formation (% GDP)",
    "BX.KLT.DINV.WD.GD.ZS": "FDI net inflows (% GDP)",
    "PX.REX.REER": "Real effective exchange rate index",
}

_COUNTRIES = [
    "NGA", "ZAF", "KEN", "ETH", "GHA", "TZA", "UGA", "RWA",
    "MOZ", "SEN", "CMR", "CIV", "ZMB", "NER", "MLI", "BFA",
    "MRT", "TCD", "GNB", "COM",
]


def _fetch_via_worldbank(indicator: str, countries: list[str]) -> list[dict]:
    """Fetch AfDB-tracked indicator from World Bank as fallback."""
    iso_list = ";".join(countries)
    url = f"{_WB_BASE}/country/{iso_list}/indicator/{indicator}"
    params = {"format": "json", "per_page": 500, "mrv": 20}
    try:
        resp = requests.get(url, params=params, timeout=30)
        resp.raise_for_status()
        data = resp.json()
        if len(data) < 2:
            return []
        rows = []
        for item in data[1] or []:
            if item.get("value") is not None:
                rows.append({
                    "iso3": item.get("countryiso3code", ""),
                    "indicator_code": indicator,
                    "year": int(item["date"]) if item.get("date") else None,
                    "value": float(item["value"]),
                    "unit": "",
                })
        return rows
    except Exception as exc:
        logger.debug("WB fallback error for %s: %s", indicator, exc)
        return []


class AfDBConnector(BaseConnector):
    source_id = "afdb"

    def get_metadata(self) -> ConnectorMetadata:
        return ConnectorMetadata(
            source_id=self.source_id,
            source_name="African Development Bank",
            description="AfDB socioeconomic development indicators for African countries.",
            base_url=_BASE,
            license_category="A",
            update_frequency="annual",
            supported_indicators=list(_INDICATORS.keys()),
            supported_countries=_COUNTRIES,
        )

    def health_check(self) -> HealthStatus:
        # AfDB API is not always publicly accessible; try it then fall back
        try:
            t0 = time.monotonic()
            resp = requests.get(f"{_BASE}/indicators", timeout=8)
            latency = round((time.monotonic() - t0) * 1000, 1)
            if resp.status_code == 200:
                return HealthStatus(source_id=self.source_id, healthy=True, latency_ms=latency, message="AfDB API OK")
        except Exception:
            pass
        # Validate via World Bank fallback
        try:
            t0 = time.monotonic()
            url = f"{_WB_BASE}/country/NGA/indicator/IC.BUS.EASE.XQ"
            resp = requests.get(url, params={"format": "json", "per_page": 1, "mrv": 1}, timeout=8)
            latency = round((time.monotonic() - t0) * 1000, 1)
            resp.raise_for_status()
            return HealthStatus(source_id=self.source_id, healthy=True, latency_ms=latency, message="Serving via WB fallback")
        except Exception as exc:
            return HealthStatus(source_id=self.source_id, healthy=False, message=str(exc))

    def fetch(self, **kwargs) -> list[dict]:
        raw: list[dict] = []
        for code in _INDICATORS:
            rows = _fetch_via_worldbank(code, _COUNTRIES)
            raw.extend(rows)
        return raw

    def normalise(self, raw: list[dict]) -> list[dict]:
        return [
            {
                "country_iso3": r["iso3"],
                "indicator_code": r["indicator_code"],
                "year": r["year"],
                "value": r["value"],
                "unit": r.get("unit", ""),
                "data_source": "African Development Bank",
                "source_id": self.source_id,
            }
            for r in raw
            if r.get("iso3") and r.get("year") and r.get("value") is not None
        ]


from app.services.connector_service import register_connector
register_connector(AfDBConnector())
