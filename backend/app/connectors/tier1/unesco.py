"""UNESCO Institute for Statistics (UIS) connector."""
from __future__ import annotations

import logging
import time
import requests

from app.connectors.base import BaseConnector, ConnectorMetadata, HealthStatus

logger = logging.getLogger(__name__)

_BASE = "https://api.uis.unesco.org/sdmx/v2"

_INDICATORS = {
    "XGDP_FSGOV": "Government expenditure on education (% GDP)",
    "NERT_1_CP": "Net enrolment rate, primary",
    "NERT_2_CP": "Net enrolment rate, lower secondary",
    "LR.AG15T24": "Youth literacy rate (15-24)",
    "PTRHBS":     "Pupil-teacher ratio, primary",
}

_COUNTRIES = [
    "NGA", "ZAF", "KEN", "ETH", "GHA", "TZA", "UGA", "RWA",
    "MOZ", "SEN", "CIV", "CMR", "NER", "MLI", "BFA",
]


class UNESCOConnector(BaseConnector):
    source_id = "unesco_uis"

    def get_metadata(self) -> ConnectorMetadata:
        return ConnectorMetadata(
            source_id=self.source_id,
            source_name="UNESCO Institute for Statistics",
            description="UIS education indicators for African countries.",
            base_url=_BASE,
            license_category="A",
            update_frequency="annual",
            supported_indicators=list(_INDICATORS.keys()),
            supported_countries=_COUNTRIES,
        )

    def health_check(self) -> HealthStatus:
        url = f"{_BASE}/dataflow/UNESCO/all"
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
        country_list = "+".join(_COUNTRIES)
        for code in _INDICATORS:
            url = f"{_BASE}/data/dataflow/UNESCO/{code}/1.0/{country_list}"
            params = {"format": "jsondata", "startPeriod": "2000", "endPeriod": "2023"}
            try:
                resp = requests.get(url, params=params, timeout=30)
                resp.raise_for_status()
                payload = resp.json()
                dataset = payload.get("data", {}).get("dataSets", [{}])[0]
                structure = payload.get("data", {}).get("structure", {})
                dims = structure.get("dimensions", {}).get("observation", [])
                time_idx = next((i for i, d in enumerate(dims) if d.get("id") == "TIME_PERIOD"), 1)
                country_dim = next((d for d in structure.get("dimensions", {}).get("series", []) if d.get("id") == "REF_AREA"), None)
                countries_map = {str(i): v.get("id", "") for i, v in enumerate(country_dim.get("values", []))} if country_dim else {}
                for series_key, series in dataset.get("series", {}).items():
                    parts = series_key.split(":")
                    country_idx = parts[0] if parts else "0"
                    iso3 = countries_map.get(country_idx, "")
                    for obs_key, obs_vals in series.get("observations", {}).items():
                        obs_parts = obs_key.split(":")
                        time_dim_vals = dims[time_idx].get("values", []) if time_idx < len(dims) else []
                        year_str = time_dim_vals[int(obs_parts[0])].get("id", "") if obs_parts and int(obs_parts[0]) < len(time_dim_vals) else ""
                        value = obs_vals[0] if obs_vals else None
                        if iso3 and year_str and value is not None:
                            raw.append({"iso3": iso3, "indicator_code": code, "year": int(year_str[:4]), "value": value})
            except Exception as exc:
                logger.warning("UNESCO fetch error for %s: %s", code, exc)
        return raw

    def normalise(self, raw: list[dict]) -> list[dict]:
        return [
            {
                "country_iso3": r["iso3"],
                "indicator_code": r["indicator_code"],
                "year": r["year"],
                "value": float(r["value"]) if r.get("value") is not None else None,
                "unit": "",
                "data_source": "UNESCO Institute for Statistics",
                "source_id": self.source_id,
            }
            for r in raw
        ]


from app.services.connector_service import register_connector
register_connector(UNESCOConnector())
