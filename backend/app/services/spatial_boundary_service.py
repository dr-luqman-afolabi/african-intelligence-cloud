"""Africa-wide administrative boundary storage.

Geometry is stored as GeoJSON in a JSON column (no PostGIS dependency).
GADM, HDX/OCHA COD-AB, and Natural Earth all distribute plain GeoJSON or
Shapefiles, so a single ingestion path (via geopandas) covers every source —
only the metadata (source/year/license) differs between them.
"""
import logging
import tempfile
import zipfile
from pathlib import Path

import geopandas as gpd
import pandas as pd
from fastapi import HTTPException
from shapely.geometry import mapping
from sqlalchemy.orm import Session

from app.models.spatial import SpatialBoundary, SpatialUnit

logger = logging.getLogger(__name__)

_NAME_CANDIDATES = [
    "shapeName", "ADM1_EN", "ADM2_EN", "ADM3_EN", "ADM0_EN", "NAME_EN",
    "NAME_1", "NAME_2", "NAME_3", "NAME_0", "NAME", "admin_name", "name",
]
_CODE_CANDIDATES = [
    "shapeISO", "GID_1", "GID_2", "GID_3", "GID_0",
    "ADM1_PCODE", "ADM2_PCODE", "ADM3_PCODE", "HASC_1", "HASC_2",
    "admin_code", "pcode", "PCODE",
]


def _guess_field(columns, candidates: list[str]) -> str | None:
    lower_to_actual = {str(c).lower(): c for c in columns}
    for candidate in candidates:
        if candidate.lower() in lower_to_actual:
            return lower_to_actual[candidate.lower()]
    return None


def _read_boundary_gdf(content: bytes, filename: str) -> gpd.GeoDataFrame:
    """Read GeoJSON or a zipped shapefile into a GeoDataFrame reprojected to EPSG:4326."""
    ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_path = Path(tmp_dir)
        if ext == "zip":
            zip_path = tmp_path / "upload.zip"
            zip_path.write_bytes(content)
            with zipfile.ZipFile(zip_path) as zf:
                zf.extractall(tmp_path)
            shp_files = list(tmp_path.rglob("*.shp"))
            if not shp_files:
                raise HTTPException(status_code=422, detail="No .shp file found inside the uploaded ZIP archive")
            gdf = gpd.read_file(shp_files[0])
        elif ext in ("geojson", "json"):
            geo_path = tmp_path / f"upload.{ext}"
            geo_path.write_bytes(content)
            gdf = gpd.read_file(geo_path)
        else:
            raise HTTPException(
                status_code=422,
                detail=f"Unsupported boundary file type '.{ext}'. Allowed: .zip (shapefile), .geojson, .json",
            )

        if gdf.empty:
            raise HTTPException(status_code=422, detail="Boundary file contains no features")

        gdf = gdf.set_crs("EPSG:4326") if gdf.crs is None else gdf.to_crs("EPSG:4326")
        return gdf


def ingest_boundary_file(
    db: Session,
    content: bytes,
    filename: str,
    country: str,
    iso3: str,
    admin_level: str,
    source: str,
    year: int | None,
    license: str | None,
    name_field: str | None,
    code_field: str | None,
    current_user,
) -> dict:
    gdf = _read_boundary_gdf(content, filename)

    name_col = name_field or _guess_field(gdf.columns, _NAME_CANDIDATES)
    if not name_col:
        raise HTTPException(
            status_code=422,
            detail=f"Could not determine the admin name field — pass name_field explicitly. "
            f"Available columns: {[c for c in gdf.columns if c != 'geometry']}",
        )
    code_col = code_field or _guess_field(gdf.columns, _CODE_CANDIDATES)

    iso3 = iso3.upper()
    units_created = 0
    units_updated = 0
    boundaries_created = 0

    for _, row in gdf.iterrows():
        admin_name = str(row[name_col])
        admin_code = str(row[code_col]) if code_col and pd.notna(row.get(code_col)) else None

        query = db.query(SpatialUnit).filter(SpatialUnit.iso3 == iso3, SpatialUnit.admin_level == admin_level)
        unit = query.filter(SpatialUnit.admin_code == admin_code).first() if admin_code else None
        if unit is None:
            unit = query.filter(SpatialUnit.admin_name == admin_name).first()

        if unit is None:
            unit = SpatialUnit(
                country=country, iso3=iso3, admin_level=admin_level,
                admin_name=admin_name, admin_code=admin_code,
            )
            db.add(unit)
            db.flush()
            units_created += 1
        else:
            units_updated += 1

        db.add(SpatialBoundary(
            unit_id=unit.id,
            source=source,
            year=year,
            geometry=mapping(row.geometry),
            crs="EPSG:4326",
            license=license,
            uploaded_by=current_user.id if current_user else None,
        ))
        boundaries_created += 1

    db.commit()
    return {
        "country": country, "iso3": iso3, "admin_level": admin_level, "source": source,
        "units_created": units_created, "units_updated": units_updated, "boundaries_created": boundaries_created,
    }


def list_boundaries(db: Session, iso3: str | None = None, admin_level: str | None = None) -> tuple[list[dict], int]:
    query = db.query(SpatialUnit)
    if iso3:
        query = query.filter(SpatialUnit.iso3 == iso3.upper())
    if admin_level:
        query = query.filter(SpatialUnit.admin_level == admin_level)
    units = query.order_by(SpatialUnit.iso3, SpatialUnit.admin_name).all()

    items = []
    for unit in units:
        if not unit.boundaries:
            continue
        latest = max(unit.boundaries, key=lambda b: b.created_at)
        items.append({
            "unit_id": unit.id, "country": unit.country, "iso3": unit.iso3,
            "admin_level": unit.admin_level, "admin_name": unit.admin_name, "admin_code": unit.admin_code,
            "source": latest.source, "year": latest.year, "license": latest.license,
        })
    return items, len(items)


def get_boundaries_geojson(db: Session, iso3: str, admin_level: str | None = None) -> dict:
    query = db.query(SpatialUnit).filter(SpatialUnit.iso3 == iso3.upper())
    if admin_level:
        query = query.filter(SpatialUnit.admin_level == admin_level)
    units = query.all()

    features = []
    for unit in units:
        if not unit.boundaries:
            continue
        latest = max(unit.boundaries, key=lambda b: b.created_at)
        features.append({
            "type": "Feature",
            "geometry": latest.geometry,
            "properties": {
                "unit_id": str(unit.id), "country": unit.country, "iso3": unit.iso3,
                "admin_level": unit.admin_level, "admin_name": unit.admin_name,
                "admin_code": unit.admin_code, "source": latest.source, "year": latest.year,
            },
        })
    if not features:
        raise HTTPException(status_code=404, detail=f"No boundaries found for {iso3}")
    return {"type": "FeatureCollection", "features": features}
