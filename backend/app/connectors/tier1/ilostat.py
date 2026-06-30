"""ILO ILOSTAT connector — labour statistics."""
from __future__ import annotations

import logging
import time
import requests

from app.connectors.base import BaseConnector, ConnectorMetadata, HealthStatus

logger = logging.getLogger(__name__)

_BASE = "https://sdmx.ilo.org/rest"

_INDICATORS = {
    "UNE_TUNE_SEX_AGE_NB": "Unemployment by sex and age",
    "EAP_TEAP_SEX_AGE_RT":  "Labour force participation rate",
    "EMP_TEMP_SEX_ECO_NB":  "Employment by economic activity",
    "LAP_2EMP_SEX_ECO_NB":  "Working poverty rate",
}

_COUNTRIES = [
    "NGA", "ZAF", "KEN", "ETH", "GHA", "TZA", "UGA", "RWA",
    "MOZ", "SEN", "CMR", "CIV", "NER", "ZMB", "MLI",
]


class ILOSTATConnector(BaseConnector):
    source_id = "ilo_ilostat"

    def get_metadata(self) -> ConnectorMetadata:
        return ConnectorMetadata(
            source_id=self.source_id,
            source_name="ILO ILOSTAT",
            description="ILO labour statistics for African countries via SDMX API.",
            base_url=_BASE,
            license_category="A",
            update_frequency="annual",
            supported_indicators=list(_INDICATORS.keys()),
            supported_countries=_COUNTRIES,
        )

    def health_check(self) -> HealthStatus:
        url = f"{_BASE}/data/ILO,UNE_TUNE_SEX_AGE_NB,1.0/NGA.BA_323.SEX_T.AGE_YTHADULT_YGE15?format=genericdata&startPeriod=2022"
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
            url = f"{_BASE}/data/ILO,{code},1.0/{country_list}"
            params = {"format": "jsondata", "startPeriod": "2010"}
            try:
                resp = requests.get(url, params=params, timeout=40)
                if resp.status_code == 404:
                    continue
                resp.raise_for_status()
                payload = resp.json()
                dataset = payload.get("data", {}).get("dataSets", [{}])[0]
                structure = payload.get("data", {}).get("structure", {})
                series_dims = structure.get("dimensions", {}).get("series", [])
                obs_dims = structure.get("dimensions", {}).get("observation", [])
                ref_area_dim = next((d for d in series_dims if d.get("id") == "REF_AREA"), None)
                time_dim = next((d for d in obs_dims if d.get("id") == "TIME_PERIOD"), None)
                if not ref_area_dim or not time_dim:
                    continue
                country_map = {str(i): v.get("id", "") for i, v in enumerate(ref_area_dim.get("values", []))}
                time_vals = [v.get("id", "") for v in time_dim.get("values", [])]
                for series_key, series in dataset.get("series", {}).items():
                    parts = series_key.split(":")
                    iso3 = country_map.get(parts[0], "") if parts else ""
                    for obs_key, obs in series.get("observations", {}).items():
                        t_idx = int(obs_key.split(":")[0])
                        year_str = time_vals[t_idx] if t_idx < len(time_vals) else ""
                        value = obs[0] if obs else None
                        if iso3 and year_str and value is not None:
                            raw.append({"iso3": iso3, "indicator_code": code, "year": int(year_str[:4]), "value": float(value)})
            except Exception as exc:
                logger.warning("ILOSTAT fetch error for %s: %s", code, exc)
        return raw

    def normalise(self, raw: list[dict]) -> list[dict]:
        return [
            {
                "country_iso3": r["iso3"],
                "indicator_code": r["indicator_code"],
                "year": r["year"],
                "value": r["value"],
                "unit": "",
                "data_source": "ILO ILOSTAT",
                "source_id": self.source_id,
            }
            for r in raw
        ]


from app.services.connector_service import register_connector
register_connector(ILOSTATConnector())
