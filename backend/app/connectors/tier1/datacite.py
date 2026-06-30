"""DataCite metadata harvesting connector.

DataCite is the leading DOI registration agency for research data. Its REST API
(https://api.datacite.org) exposes metadata for millions of scholarly datasets.
This connector harvests African research dataset metadata to build AIC's DOI
index and support automatic citation and lineage tracking.
"""
from __future__ import annotations

import logging
import time
import requests

from app.connectors.base import BaseConnector, ConnectorMetadata, HealthStatus

logger = logging.getLogger(__name__)

_API_BASE = "https://api.datacite.org"

# Affiliation country codes covering African research institutions
_AFRICA_RORS = [
    "ZA", "NG", "ET", "KE", "GH", "TZ", "ZM", "UG", "RW", "MZ",
    "CM", "SN", "CI", "MA", "EG", "TN", "DZ",
]

# Resource types to harvest
_RESOURCE_TYPES = ["Dataset", "Collection", "Software"]

# Subject/topic filters for African development data
_SUBJECTS = [
    "Africa", "household survey", "poverty", "health", "agriculture",
    "economic development", "climate change",
]


class DataCiteConnector(BaseConnector):
    source_id = "datacite"

    def get_metadata(self) -> ConnectorMetadata:
        return ConnectorMetadata(
            source_id=self.source_id,
            source_name="DataCite Research Data Catalog",
            description=(
                "DataCite DOI registry — research datasets and collections with "
                "African affiliations or African development topics."
            ),
            base_url=_API_BASE,
            license_category="A",
            update_frequency="continuous",
            supported_countries=_AFRICA_RORS,
        )

    def health_check(self) -> HealthStatus:
        url = f"{_API_BASE}/heartbeat"
        try:
            t0 = time.monotonic()
            resp = requests.get(url, timeout=8)
            latency = round((time.monotonic() - t0) * 1000, 1)
            if resp.status_code == 200:
                return HealthStatus(
                    source_id=self.source_id,
                    healthy=True,
                    latency_ms=latency,
                    message="DataCite API heartbeat OK",
                )
            return HealthStatus(source_id=self.source_id, healthy=False,
                                message=f"HTTP {resp.status_code}")
        except Exception as exc:
            return HealthStatus(source_id=self.source_id, healthy=False, message=str(exc))

    def fetch(self, **kwargs) -> list[dict]:
        """Harvest DOI metadata for African research datasets."""
        raw: list[dict] = []
        page_size = 100
        max_pages = 5  # cap at 500 records per sync

        for subject in _SUBJECTS[:3]:  # rotate subjects across syncs
            url = f"{_API_BASE}/dois"
            params = {
                "query": f"subjects.subject:{subject!r} AND resourceTypeGeneral:Dataset",
                "affiliation": "true",
                "page[size]": page_size,
                "page[number]": 1,
                "sort": "-publicationYear",
            }
            try:
                resp = requests.get(url, params=params, timeout=30)
                resp.raise_for_status()
                body = resp.json()
                for item in body.get("data", []):
                    attrs = item.get("attributes", {})
                    doi = attrs.get("doi", "")
                    pub_year = attrs.get("publicationYear")
                    titles = attrs.get("titles", [])
                    title = titles[0].get("title", "") if titles else ""

                    # Extract country/ISO from geo locations if present
                    geo = attrs.get("geoLocations", [])
                    iso3 = _extract_iso3(geo, attrs)

                    raw.append({
                        "doi": doi,
                        "iso3": iso3 or "ZZZ",  # ZZZ = unresolved
                        "indicator_code": f"DATACITE_{doi.replace('/', '_').replace('.', '_')}",
                        "year": pub_year,
                        "value": 1,
                        "unit": "dataset",
                        "title": title,
                        "publisher": attrs.get("publisher", ""),
                        "resource_type": attrs.get("types", {}).get("resourceTypeGeneral", "Dataset"),
                        "license_url": _extract_license(attrs),
                    })
            except Exception as exc:
                logger.debug("DataCite fetch error for subject=%s: %s", subject, exc)

        return raw

    def normalise(self, raw: list[dict]) -> list[dict]:
        out = []
        for r in raw:
            if not r.get("year"):
                continue
            out.append({
                "country_iso3": r["iso3"],
                "indicator_code": r["indicator_code"],
                "year": int(r["year"]),
                "value": float(r["value"]),
                "unit": r.get("unit", "dataset"),
                "data_source": "DataCite",
                "source_id": self.source_id,
                "metadata": {
                    "doi": r.get("doi", ""),
                    "title": r.get("title", ""),
                    "publisher": r.get("publisher", ""),
                    "resource_type": r.get("resource_type", "Dataset"),
                    "license_url": r.get("license_url", ""),
                },
            })
        return out


def _extract_iso3(geo_locations: list, attrs: dict) -> str:
    """Best-effort ISO3 extraction from DataCite attributes."""
    for gl in geo_locations:
        country = gl.get("geoLocationPlace", "")
        if country:
            return _PLACE_TO_ISO3.get(country.title(), "")
    # Try affiliation country
    creators = attrs.get("creators", [])
    for creator in creators:
        for aff in creator.get("affiliation", []):
            country = aff.get("affiliationIdentifier", "")
            if country:
                return country[:3].upper()
    return ""


def _extract_license(attrs: dict) -> str:
    for right in attrs.get("rightsList", []):
        url = right.get("rightsUri", "")
        if url:
            return url
    return ""


_PLACE_TO_ISO3 = {
    "Nigeria": "NGA", "Ethiopia": "ETH", "Kenya": "KEN", "Ghana": "GHA",
    "Tanzania": "TZA", "Uganda": "UGA", "Rwanda": "RWA", "Mozambique": "MOZ",
    "Zambia": "ZMB", "Cameroon": "CMR", "Senegal": "SEN", "South Africa": "ZAF",
    "Egypt": "EGY", "Morocco": "MAR", "Tunisia": "TUN", "Algeria": "DZA",
    "Malawi": "MWI", "Niger": "NER", "Mali": "MLI", "Burkina Faso": "BFA",
    "Madagascar": "MDG", "Zimbabwe": "ZWE", "Sudan": "SDN",
}


from app.services.connector_service import register_connector
register_connector(DataCiteConnector())
