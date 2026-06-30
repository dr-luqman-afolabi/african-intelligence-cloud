"""OpenStreetMap connector — infrastructure and geospatial data via Overpass API."""
from __future__ import annotations

import logging
import time
import requests

from app.connectors.base import BaseConnector, ConnectorMetadata, HealthStatus

logger = logging.getLogger(__name__)

_OVERPASS_API = "https://overpass-api.de/api/interpreter"
_BASE = "https://www.openstreetmap.org"

# ISO3 → Overpass relation IDs for country boundaries
_COUNTRY_RELATIONS = {
    "NGA": 192798, "ETH": 192790, "KEN": 192798,
    "TZA": 195270, "GHA": 192781, "UGA": 192796,
    "ZAF": 87565, "SEN": 192775, "EGY": 1473947, "MAR": 3630439,
}

_INDICATORS = {
    "OSM_HOSPITALS": "Number of hospitals",
    "OSM_SCHOOLS": "Number of schools",
    "OSM_ROAD_KM": "Road network length (km)",
}


class OSMConnector(BaseConnector):
    source_id = "osm"

    def get_metadata(self) -> ConnectorMetadata:
        return ConnectorMetadata(
            source_id=self.source_id,
            source_name="OpenStreetMap",
            description="OSM via Overpass API — infrastructure features (hospitals, schools, roads) by country.",
            base_url=_BASE,
            license_category="A",
            update_frequency="weekly",
            supported_indicators=list(_INDICATORS.keys()),
            supported_countries=list(_COUNTRY_RELATIONS.keys()),
        )

    def health_check(self) -> HealthStatus:
        try:
            t0 = time.monotonic()
            resp = requests.get(
                _OVERPASS_API,
                params={"data": "[out:json];node(1);out;"},
                timeout=10,
            )
            latency = round((time.monotonic() - t0) * 1000, 1)
            return HealthStatus(
                source_id=self.source_id,
                healthy=resp.status_code == 200,
                latency_ms=latency,
                message=f"Overpass API HTTP {resp.status_code}",
            )
        except Exception as exc:
            return HealthStatus(source_id=self.source_id, healthy=False, message=str(exc))

    def _count_features(self, relation_id: int, amenity: str) -> int | None:
        query = f"""
[out:json][timeout:30];
area(id:{3600000000 + relation_id})->.searchArea;
(
  node["amenity"="{amenity}"](area.searchArea);
  way["amenity"="{amenity}"](area.searchArea);
);
out count;
"""
        try:
            resp = requests.post(_OVERPASS_API, data={"data": query}, timeout=35)
            if resp.status_code != 200:
                return None
            return int(resp.json()["elements"][0].get("tags", {}).get("total", 0) or 0)
        except Exception:
            return None

    def fetch(self, **kwargs) -> list[dict]:
        raw: list[dict] = []
        for iso3, rel_id in _COUNTRY_RELATIONS.items():
            for amenity, code in [("hospital", "OSM_HOSPITALS"), ("school", "OSM_SCHOOLS")]:
                count = self._count_features(rel_id, amenity)
                if count is not None:
                    raw.append({
                        "iso3": iso3,
                        "indicator_code": code,
                        "year": 2024,
                        "value": count,
                    })
        return raw

    def normalise(self, raw: list[dict]) -> list[dict]:
        return [
            {
                "country_iso3": r["iso3"],
                "indicator_code": r["indicator_code"],
                "year": r["year"],
                "value": float(r["value"]),
                "unit": "count",
                "data_source": "OpenStreetMap",
                "source_id": self.source_id,
            }
            for r in raw
            if r.get("iso3") and r.get("year") and r.get("value") is not None
        ]


from app.services.connector_service import register_connector
register_connector(OSMConnector())
