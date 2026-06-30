"""IMF Data API connector (JSON:API compact format)."""
from __future__ import annotations

import logging
import time
import requests

from app.connectors.base import BaseConnector, ConnectorError, ConnectorMetadata, HealthStatus

logger = logging.getLogger(__name__)

_BASE = "https://www.imf.org/external/datamapper/api/v1"

# Indicator → IMF concept code
_INDICATORS = {
    "NGDP_RPCH": {"name": "GDP Growth Rate",      "unit": "%"},
    "PCPIPCH":   {"name": "Inflation Rate (CPI)", "unit": "%"},
    "LUR":       {"name": "Unemployment Rate",    "unit": "%"},
    "BCA_NGDPD": {"name": "Current Account (% GDP)", "unit": "% of GDP"},
    "GGXWDG_NGDP": {"name": "Government Debt (% GDP)", "unit": "% of GDP"},
}

_COUNTRIES = [
    "NGA", "ZAF", "KEN", "ETH", "GHA", "EGY", "TZA", "UGA", "CIV", "SEN",
    "CMR", "MDG", "MOZ", "ZMB", "ZWE", "RWA", "MLI", "BFA", "NER", "SDN",
]


class IMFConnector(BaseConnector):
    source_id = "imf_api"

    def get_metadata(self) -> ConnectorMetadata:
        return ConnectorMetadata(
            source_id=self.source_id,
            source_name="IMF Data (World Economic Outlook)",
            description="IMF WEO macroeconomic indicators for African countries.",
            base_url=_BASE,
            license_category="A",
            update_frequency="biannual",
            supported_indicators=list(_INDICATORS.keys()),
            supported_countries=_COUNTRIES,
        )

    def health_check(self) -> HealthStatus:
        url = f"{_BASE}/NGDP_RPCH/NGA"
        try:
            t0 = time.monotonic()
            resp = requests.get(url, timeout=10)
            latency = round((time.monotonic() - t0) * 1000, 1)
            resp.raise_for_status()
            return HealthStatus(source_id=self.source_id, healthy=True, latency_ms=latency, message="OK")
        except Exception as exc:
            return HealthStatus(source_id=self.source_id, healthy=False, message=str(exc))

    def fetch(self, **kwargs) -> list[dict]:
        raw: list[dict] = []
        for code in _INDICATORS:
            url = f"{_BASE}/{code}"
            try:
                resp = requests.get(url, timeout=20)
                resp.raise_for_status()
                data = resp.json().get("values", {}).get(code, {})
                for iso3 in _COUNTRIES:
                    iso3_upper = iso3.upper()
                    series = data.get(iso3_upper, {})
                    for year_str, value in series.items():
                        if value is not None:
                            raw.append({"iso3": iso3_upper, "indicator_code": code, "year": int(year_str), "value": float(value)})
            except Exception as exc:
                logger.warning("IMF fetch error for %s: %s", code, exc)
        return raw

    def normalise(self, raw: list[dict]) -> list[dict]:
        return [
            {
                "country_iso3": r["iso3"],
                "indicator_code": r["indicator_code"],
                "year": r["year"],
                "value": r["value"],
                "unit": _INDICATORS.get(r["indicator_code"], {}).get("unit", ""),
                "data_source": "IMF World Economic Outlook",
                "source_id": self.source_id,
            }
            for r in raw
        ]


from app.services.connector_service import register_connector
register_connector(IMFConnector())
