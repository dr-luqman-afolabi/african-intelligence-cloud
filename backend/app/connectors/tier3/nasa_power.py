"""NASA POWER connector — meteorological and solar energy data."""
from __future__ import annotations

import logging
import time
import requests

from app.connectors.base import BaseConnector, ConnectorMetadata, HealthStatus

logger = logging.getLogger(__name__)

_BASE = "https://power.larc.nasa.gov/api/temporal/climatology/point"

# Representative city coordinates for 10 African countries
_LOCATIONS = {
    "NGA": (9.0765, 7.3986, "Abuja"),
    "ETH": (9.0054, 38.7636, "Addis Ababa"),
    "KEN": (-1.2921, 36.8219, "Nairobi"),
    "TZA": (-6.7924, 39.2083, "Dar es Salaam"),
    "GHA": (5.5600, -0.2057, "Accra"),
    "ZAF": (-25.7479, 28.2293, "Pretoria"),
    "EGY": (30.0444, 31.2357, "Cairo"),
    "MAR": (33.9716, -6.8498, "Rabat"),
    "CMR": (3.8480, 11.5021, "Yaoundé"),
    "SEN": (14.6928, -17.4467, "Dakar"),
}

_PARAMETERS = ["T2M", "PRECTOTCORR", "ALLSKY_SFC_SW_DWN"]


class NASAPOWERConnector(BaseConnector):
    source_id = "nasa_power"

    def get_metadata(self) -> ConnectorMetadata:
        return ConnectorMetadata(
            source_id=self.source_id,
            source_name="NASA POWER",
            description="NASA POWER — temperature, precipitation, and solar irradiance climatology data.",
            base_url="https://power.larc.nasa.gov",
            license_category="A",
            update_frequency="annual",
            supported_indicators=_PARAMETERS,
            supported_countries=list(_LOCATIONS.keys()),
        )

    def health_check(self) -> HealthStatus:
        url = "https://power.larc.nasa.gov/api/temporal/climatology/point"
        params = {
            "parameters": "T2M",
            "community": "RE",
            "longitude": 7.3986,
            "latitude": 9.0765,
            "format": "JSON",
        }
        try:
            t0 = time.monotonic()
            resp = requests.get(url, params=params, timeout=15)
            latency = round((time.monotonic() - t0) * 1000, 1)
            return HealthStatus(
                source_id=self.source_id,
                healthy=resp.status_code == 200,
                latency_ms=latency,
                message=f"NASA POWER HTTP {resp.status_code}",
            )
        except Exception as exc:
            return HealthStatus(source_id=self.source_id, healthy=False, message=str(exc))

    def fetch(self, **kwargs) -> list[dict]:
        raw: list[dict] = []
        for iso3, (lat, lon, _city) in _LOCATIONS.items():
            params = {
                "parameters": ",".join(_PARAMETERS),
                "community": "RE",
                "longitude": lon,
                "latitude": lat,
                "format": "JSON",
            }
            try:
                resp = requests.get(_BASE, params=params, timeout=30)
                if resp.status_code != 200:
                    continue
                data = resp.json().get("properties", {}).get("parameter", {})
                for param, monthly_vals in data.items():
                    annual_val = monthly_vals.get("ANN")
                    if annual_val is not None:
                        raw.append({
                            "iso3": iso3,
                            "indicator_code": f"NASA_{param}",
                            "year": 2022,
                            "value": annual_val,
                        })
            except Exception as exc:
                logger.debug("NASA POWER fetch error for %s: %s", iso3, exc)
        return raw

    def normalise(self, raw: list[dict]) -> list[dict]:
        units = {
            "NASA_T2M": "°C",
            "NASA_PRECTOTCORR": "mm/day",
            "NASA_ALLSKY_SFC_SW_DWN": "kWh/m²/day",
        }
        return [
            {
                "country_iso3": r["iso3"],
                "indicator_code": r["indicator_code"],
                "year": r["year"],
                "value": float(r["value"]),
                "unit": units.get(r["indicator_code"], ""),
                "data_source": "NASA POWER",
                "source_id": self.source_id,
            }
            for r in raw
            if r.get("iso3") and r.get("year") and r.get("value") is not None
        ]


from app.services.connector_service import register_connector
register_connector(NASAPOWERConnector())
