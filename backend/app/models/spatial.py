import uuid
import enum
from sqlalchemy import Column, String, Integer, DateTime, Uuid, ForeignKey, Enum, JSON, Index
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base


class AdminLevel(str, enum.Enum):
    ADM0 = "ADM0"
    ADM1 = "ADM1"
    ADM2 = "ADM2"
    ADM3 = "ADM3"


class BoundarySource(str, enum.Enum):
    GADM = "gadm"
    HDX = "hdx"
    OCHA_COD_AB = "ocha_cod_ab"
    NATURAL_EARTH = "natural_earth"
    CUSTOM_UPLOAD = "custom_upload"


class SpatialUnit(Base):
    """A canonical administrative unit (country/province/district/...) independent of geometry vintage."""

    __tablename__ = "spatial_units"

    id = Column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    country = Column(String(255), nullable=False)
    iso3 = Column(String(3), nullable=False, index=True)
    admin_level = Column(Enum(AdminLevel), nullable=False)
    admin_name = Column(String(500), nullable=False)
    admin_code = Column(String(100), nullable=True)
    parent_unit_id = Column(Uuid(as_uuid=True), ForeignKey("spatial_units.id", ondelete="SET NULL"), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    parent = relationship("SpatialUnit", remote_side=[id])
    boundaries = relationship("SpatialBoundary", back_populates="unit", cascade="all, delete-orphan")

    __table_args__ = (
        Index("ix_spatial_units_iso3_level", "iso3", "admin_level"),
    )


class SpatialBoundary(Base):
    """A specific geometry realization (source + year) for a spatial unit."""

    __tablename__ = "spatial_boundaries"

    id = Column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    unit_id = Column(Uuid(as_uuid=True), ForeignKey("spatial_units.id", ondelete="CASCADE"), nullable=False)
    source = Column(Enum(BoundarySource), nullable=False)
    year = Column(Integer, nullable=True)
    geometry = Column(JSON, nullable=False)  # GeoJSON geometry object
    crs = Column(String(50), nullable=False, default="EPSG:4326")
    license = Column(String(255), nullable=True)
    uploaded_by = Column(Uuid(as_uuid=True), ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    unit = relationship("SpatialUnit", back_populates="boundaries")

    __table_args__ = (
        Index("ix_spatial_boundaries_unit", "unit_id"),
    )
