"""DHS Program connector — Demographic and Health Surveys."""
from __future__ import annotations

import logging
import time
import requests

from app.config import get_settings
from app.connectors.base import BaseConnector, ConnectorMetadata, HealthStatus

logger = logging.getLogger(__name__)

_BASE = "https://api.dhsprogram.com/rest/dhs/v8"

_COUNTRIES = ["NG", "ZA", "KE", "ET", "GH", "TZ", "UG", "RW", "MZ", "SN"]

_INDICATORS = {
    "CM_ECMR_C_U5M": "Under-5 mortality rate",
    "CN_NUTS_C_HA2": "Stunting (% children under 5)",
    "FP_CUSA_W_MOD": "Contraceptive prevalence rate",
    "MM_MMRT_W_MMR": "Maternal mortality ratio",
    "HA_HIVP_B_HIV": "HIV prevalence (adults 15-49)",
}


class DHSConnector(BaseConnector):
    source_id = "dhs_program"

    def get_metadata(self) -> ConnectorMetadata:
        return ConnectorMetadata(
            source_id=self.source_id,
            source_name="DHS Program",
            description="Demographic and Health Surveys — nationally representative household survey data.",
            base_url=_BASE,
            license_category="B",
            update_frequency="triennial",
            supported_indicators=list(_INDICATORS.keys()),
            supported_countries=[c for c in _COUNTRIES],
        )

    def health_check(self) -> HealthStatus:
        url = f"{_BASE}/countries"
        params = {"f": "json"}
        try:
            t0 = time.monotonic()
            resp = requests.get(url, params=params, timeout=10)
            latency = round((time.monotonic() - t0) * 1000, 1)
            resp.raise_for_status()
            return HealthStatus(source_id=self.source_id, healthy=True, latency_ms=latency, message="OK")
        except Exception as exc:
            return HealthStatus(source_id=self.source_id, healthy=False, message=str(exc))

    def fetch(self, **kwargs) -> list[dict]:
        raw: list[dict] = []
        settings = get_settings()
        api_key = getattr(settings, "dhs_api_key", None)
        country_list = ",".join(_COUNTRIES)
        for code in _INDICATORS:
            url = f"{_BASE}/data"
            params = {
                "countryIds": country_list,
                "indicatorIds": code,
                "f": "json",
                "returnFields": "CountryName,Indicator,Value,ByVariableLabel,SurveyYear,DHSCC",
                "perpage": 500,
            }
            if api_key:
                params["apiKey"] = api_key
            try:
                resp = requests.get(url, params=params, timeout=30)
                resp.raise_for_status()
                for row in resp.json().get("Data", []):
                    raw.append({
                        "iso2": row.get("DHSCC", ""),
                        "indicator_code": code,
                        "year": row.get("SurveyYear"),
                        "value": row.get("Value"),
                    })
            except Exception as exc:
                logger.warning("DHS fetch error for %s: %s", code, exc)
        return raw

    def normalise(self, raw: list[dict]) -> list[dict]:
        _iso2_to_3 = {
            "NG": "NGA", "ZA": "ZAF", "KE": "KEN", "ET": "ETH", "GH": "GHA",
            "TZ": "TZA", "UG": "UGA", "RW": "RWA", "MZ": "MOZ", "SN": "SEN",
        }
        return [
            {
                "country_iso3": _iso2_to_3.get(r.get("iso2", ""), ""),
                "indicator_code": r["indicator_code"],
                "year": int(r["year"]) if r.get("year") else None,
                "value": float(r["value"]) if r.get("value") is not None else None,
                "unit": "",
                "data_source": "DHS Program",
                "source_id": self.source_id,
            }
            for r in raw
            if r.get("iso2") and r.get("value") is not None
        ]


from app.services.connector_service import register_connector
register_connector(DHSConnector())
