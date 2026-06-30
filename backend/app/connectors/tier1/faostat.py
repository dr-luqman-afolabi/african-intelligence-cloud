"""FAOSTAT connector — FAO food & agriculture statistics."""
from __future__ import annotations

import logging
import time
import requests

from app.connectors.base import BaseConnector, ConnectorMetadata, HealthStatus

logger = logging.getLogger(__name__)

_BASE = "https://fenixservices.fao.org/faostat/api/v1/en"

_DOMAINS = {
    "QCL": "Crops and livestock products",
    "FBS": "Food Balance Sheets",
    "FS":  "Food Security Indicators",
}

_AREA_CODES = [
    "231", "197", "114", "67", "59", "181", "238", "226", "145", "217",
]  # Africa country codes in FAO system (Nigeria, South Africa, Kenya, etc.)


class FAOSTATConnector(BaseConnector):
    source_id = "faostat"

    def get_metadata(self) -> ConnectorMetadata:
        return ConnectorMetadata(
            source_id=self.source_id,
            source_name="FAOSTAT",
            description="FAO food and agriculture statistics for African countries.",
            base_url=_BASE,
            license_category="A",
            update_frequency="annual",
            supported_indicators=list(_DOMAINS.keys()),
        )

    def health_check(self) -> HealthStatus:
        url = f"{_BASE}/domains"
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
        for domain_code in _DOMAINS:
            url = f"{_BASE}/data/{domain_code}"
            params = {
                "area": ",".join(_AREA_CODES),
                "year": "2010,2011,2012,2013,2014,2015,2016,2017,2018,2019,2020,2021,2022,2023",
                "show_codes": "true",
                "show_unit": "true",
                "output_type": "json",
            }
            try:
                resp = requests.get(url, params=params, timeout=60)
                resp.raise_for_status()
                for row in resp.json().get("data", []):
                    raw.append({
                        "fao_area_code": row.get("Area Code", ""),
                        "iso3": row.get("Area Code (ISO3)", ""),
                        "indicator_code": f"{domain_code}_{row.get('Item Code', '')}",
                        "indicator_name": row.get("Item", ""),
                        "element": row.get("Element", ""),
                        "year": row.get("Year"),
                        "value": row.get("Value"),
                        "unit": row.get("Unit", ""),
                        "domain": domain_code,
                    })
            except Exception as exc:
                logger.warning("FAOSTAT fetch error for domain %s: %s", domain_code, exc)
        return raw

    def normalise(self, raw: list[dict]) -> list[dict]:
        return [
            {
                "country_iso3": r["iso3"],
                "indicator_code": r["indicator_code"],
                "year": int(r["year"]) if r.get("year") else None,
                "value": float(r["value"]) if r.get("value") is not None else None,
                "unit": r.get("unit", ""),
                "data_source": "FAOSTAT",
                "source_id": self.source_id,
            }
            for r in raw
            if r.get("iso3") and r.get("value") is not None
        ]


from app.services.connector_service import register_connector
register_connector(FAOSTATConnector())
