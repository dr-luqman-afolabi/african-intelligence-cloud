"""Automatic administrative-boundary provider for spatial mapping.

When a spatial analysis has no user-uploaded boundary and no inline GeoJSON,
this fetches openly-licensed admin boundaries from geoBoundaries
(https://www.geoboundaries.org, CC-BY 4.0) so the choropleth can render on its
own. Results are cached in-process per (iso3, admin level). Every failure path
returns None so the analysis still succeeds (just without a map), exactly as
before.

Each returned feature carries ``properties.admin_name`` (from geoBoundaries'
``shapeName``) so the existing merge — which matches survey geography values
against ``admin_name`` — lights up the map when region names line up.
"""
from __future__ import annotations

import logging
from typing import Any

import requests

logger = logging.getLogger(__name__)

_GB_META = "https://www.geoboundaries.org/api/current/gbOpen/{iso3}/{adm}/"
_CACHE: dict[tuple[str, str], dict[str, Any] | None] = {}
_TIMEOUT = 12


def _adm(admin_level: Any) -> str:
    """Normalize an admin level to a geoBoundaries key: ADM0/ADM1/ADM2..."""
    if admin_level is None or admin_level == "":
        return "ADM1"
    s = str(admin_level).upper().strip()
    if s.startswith("ADM"):
        return s
    digits = "".join(ch for ch in s if ch.isdigit())
    return f"ADM{digits}" if digits else "ADM1"


def _normalize(geojson: dict[str, Any], iso3: str, adm: str) -> dict[str, Any]:
    features = []
    for feat in geojson.get("features", []):
        props = dict(feat.get("properties") or {})
        name = props.get("shapeName") or props.get("admin_name") or props.get("name")
        if name and not props.get("admin_name"):
            props["admin_name"] = name
        props.setdefault("iso3", iso3.upper())
        props.setdefault("admin_level", adm)
        props.setdefault("source", "geoBoundaries (CC-BY 4.0)")
        if feat.get("geometry"):
            features.append({"type": "Feature", "geometry": feat["geometry"], "properties": props})
    return {"type": "FeatureCollection", "features": features}


def fetch_admin_boundaries(iso3: str | None, admin_level: Any = None) -> dict[str, Any] | None:
    """Return a normalized boundary FeatureCollection for a country, or None.

    Prefers geoBoundaries' pre-simplified geometry (smaller, web-map friendly);
    falls back to the full geometry. Cached per (iso3, admin level).
    """
    if not iso3:
        return None
    iso3 = iso3.upper().strip()
    if len(iso3) != 3:
        return None
    adm = _adm(admin_level)
    cache_key = (iso3, adm)
    if cache_key in _CACHE:
        return _CACHE[cache_key]

    result: dict[str, Any] | None = None
    try:
        meta = requests.get(_GB_META.format(iso3=iso3, adm=adm), timeout=_TIMEOUT)
        meta.raise_for_status()
        info = meta.json()
        if isinstance(info, list):
            info = info[0] if info else {}
        gj_url = info.get("simplifiedGeometryGeoJSON") or info.get("gjDownloadURL")
        if gj_url:
            gj = requests.get(gj_url, timeout=_TIMEOUT)
            gj.raise_for_status()
            data = gj.json()
            if data.get("features"):
                result = _normalize(data, iso3, adm)
                logger.info("Loaded %d %s boundaries for %s from geoBoundaries",
                            len(result["features"]), adm, iso3)
    except Exception as exc:
        logger.warning("Could not fetch boundaries for %s/%s (%s); map will be empty", iso3, adm, exc)
        result = None

    _CACHE[cache_key] = result
    return result
