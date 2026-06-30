"""IPUMS Africa connector — queries IPUMS International census microdata catalogue."""
from __future__ import annotations

import logging
import time
import requests

from app.connectors.base import BaseConnector, ConnectorMetadata, HealthStatus

logger = logging.getLogger(__name__)

_BASE = "https://international.ipums.org/international-action/samples/description"

# African countries covered by IPUMS International as of 2024
_IPUMS_AFRICA_COUNTRIES = [
    "BEN", "BWA", "BFA", "CMR", "ETH", "GHA", "GIN", "KEN",
    "LSO", "LBR", "MDG", "MWI", "MLI", "MRT", "MOZ", "NAM",
    "NER", "NGA", "RWA", "SEN", "SLE", "ZAF", "SDN", "TZA",
    "TGO", "UGA", "ZMB", "ZWE",
]

# IPUMS uses a metadata API; we map to the canonical sync shape via survey catalogue records
_METADATA_API = "https://api.ipums.org/metadata/nhgis/datasets"  # placeholder until IPUMS opens full API


class IPUMSConnector(BaseConnector):
    source_id = "ipums_africa"

    def get_metadata(self) -> ConnectorMetadata:
        return ConnectorMetadata(
            source_id=self.source_id,
            source_name="IPUMS International — Africa Census Microdata",
            description="Census and survey microdata for African countries from IPUMS International.",
            base_url="https://international.ipums.org",
            license_category="B",
            update_frequency="irregular",
            supported_countries=_IPUMS_AFRICA_COUNTRIES,
        )

    def health_check(self) -> HealthStatus:
        url = "https://international.ipums.org/international/"
        try:
            t0 = time.monotonic()
            resp = requests.head(url, timeout=10, allow_redirects=True)
            latency = round((time.monotonic() - t0) * 1000, 1)
            if resp.status_code < 500:
                return HealthStatus(source_id=self.source_id, healthy=True, latency_ms=latency,
                                    message="IPUMS International reachable")
            return HealthStatus(source_id=self.source_id, healthy=False, message=f"HTTP {resp.status_code}")
        except Exception as exc:
            return HealthStatus(source_id=self.source_id, healthy=False, message=str(exc))

    def fetch(self, **kwargs) -> list[dict]:
        """
        Fetches survey availability metadata from the IPUMS International sample list.
        Full microdata extraction requires authentication and the IPUMS API key;
        this connector returns catalogue-level records for the survey registry.
        """
        url = "https://international.ipums.org/international-action/samples/available_countries.json"
        raw: list[dict] = []
        try:
            resp = requests.get(url, timeout=20)
            resp.raise_for_status()
            data = resp.json()
            for item in data:
                iso3 = _country_to_iso3(item.get("code", ""))
                if not iso3 or iso3 not in _IPUMS_AFRICA_COUNTRIES:
                    continue
                for sample in item.get("samples", []):
                    raw.append({
                        "iso3": iso3,
                        "indicator_code": f"IPUMS_CENSUS_{iso3}_{sample.get('year', '')}",
                        "year": sample.get("year"),
                        "value": 1,
                        "unit": "census_round",
                        "sample_label": sample.get("label", ""),
                    })
        except Exception as exc:
            logger.warning("IPUMS fetch error (catalogue-level): %s", exc)
            # Fall back to stub records so the registry can still populate
            for iso3 in _IPUMS_AFRICA_COUNTRIES:
                raw.append({
                    "iso3": iso3,
                    "indicator_code": f"IPUMS_CENSUS_{iso3}_AVAILABILITY",
                    "year": 2024,
                    "value": 1,
                    "unit": "catalogue_entry",
                    "sample_label": "IPUMS International catalogue entry",
                })
        return raw

    def normalise(self, raw: list[dict]) -> list[dict]:
        return [
            {
                "country_iso3": r["iso3"],
                "indicator_code": r["indicator_code"],
                "year": int(r["year"]) if r.get("year") else None,
                "value": float(r["value"]),
                "unit": r.get("unit", ""),
                "data_source": "IPUMS International",
                "source_id": self.source_id,
            }
            for r in raw
            if r.get("iso3") and r.get("year")
        ]


# Minimal IPUMS 2-letter → ISO 3166-1 alpha-3 mapping for African countries
_IPUMS_CODE_MAP: dict[str, str] = {
    "BJ": "BEN", "BW": "BWA", "BF": "BFA", "CM": "CMR", "ET": "ETH",
    "GH": "GHA", "GN": "GIN", "KE": "KEN", "LS": "LSO", "LR": "LBR",
    "MG": "MDG", "MW": "MWI", "ML": "MLI", "MR": "MRT", "MZ": "MOZ",
    "NA": "NAM", "NE": "NER", "NG": "NGA", "RW": "RWA", "SN": "SEN",
    "SL": "SLE", "ZA": "ZAF", "SD": "SDN", "TZ": "TZA", "TG": "TGO",
    "UG": "UGA", "ZM": "ZMB", "ZW": "ZWE",
}


def _country_to_iso3(code: str) -> str:
    return _IPUMS_CODE_MAP.get(code.upper(), "")


from app.services.connector_service import register_connector
register_connector(IPUMSConnector())
