from __future__ import annotations

import uuid
import enum

from sqlalchemy import (
    Column, String, Boolean, Integer, BigInteger, ForeignKey,
    Enum, DateTime, JSON, Text, Uuid, Index,
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.database import Base


class MicrodataAccessStatus(str, enum.Enum):
    OPEN = "open"
    REQUIRES_REGISTRATION = "requires_registration"
    REQUIRES_APPROVAL = "requires_approval"
    USER_UPLOAD = "user_upload"
    RESTRICTED = "restricted"


class MicrodataFileType(str, enum.Enum):
    CSV = "csv"
    XLSX = "xlsx"
    DTA = "dta"
    SAV = "sav"


class MicrodataJobStatus(str, enum.Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class MicrodataJobType(str, enum.Enum):
    POVERTY = "poverty"
    SPATIAL_POVERTY = "spatial_poverty"
    AGRICULTURE = "agriculture"
    DIVERSIFICATION = "diversification"
    SPATIAL_AGRICULTURE = "spatial_agriculture"
    SPATIAL_DIVERSIFICATION = "spatial_diversification"


class StandardConcept(str, enum.Enum):
    """Canonical LSMS-family concepts that raw survey variables get mapped to,
    so poverty/agriculture/diversification analysis can run the same way
    regardless of each survey's own column-naming conventions."""
    HOUSEHOLD_ID = "household_id"
    COUNTRY = "country"
    REGION = "region"
    PROVINCE = "province"
    DISTRICT = "district"
    SECTOR = "sector"
    URBAN_RURAL = "urban_rural"
    GENDER = "gender"
    AGE = "age"
    EDUCATION = "education"
    HOUSEHOLD_SIZE = "household_size"
    WELFARE = "welfare"
    CONSUMPTION = "consumption"
    INCOME = "income"
    WEIGHT = "weight"
    STRATA = "strata"
    CLUSTER = "cluster"
    LAND_AREA = "land_area"
    CROP_OUTPUT = "crop_output"
    CROP_VALUE = "crop_value"
    LIVESTOCK = "livestock"
    FERTILIZER = "fertilizer"
    IMPROVED_SEED = "improved_seed"
    IRRIGATION = "irrigation"
    EXTENSION = "extension"
    POVERTY_STATUS = "poverty_status"


class MicrodataProject(Base):
    __tablename__ = "microdata_projects"

    id = Column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    country_iso3 = Column(String(3), nullable=True)
    owner_id = Column(Uuid(as_uuid=True), ForeignKey("users.id"), nullable=False)
    organization_id = Column(Uuid(as_uuid=True), ForeignKey("organizations.id"), nullable=True)
    access_status = Column(Enum(MicrodataAccessStatus), nullable=False, default=MicrodataAccessStatus.USER_UPLOAD)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    owner = relationship("User", foreign_keys=[owner_id])
    datasets = relationship("MicrodataDataset", back_populates="project", cascade="all, delete-orphan")


class MicrodataDataset(Base):
    __tablename__ = "microdata_datasets"

    id = Column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_id = Column(Uuid(as_uuid=True), ForeignKey("microdata_projects.id"), nullable=True)
    name = Column(String(255), nullable=False)
    original_filename = Column(String(500), nullable=False)
    file_type = Column(Enum(MicrodataFileType), nullable=False)
    storage_path = Column(String(1000), nullable=False)
    file_size_bytes = Column(BigInteger, nullable=True)

    country_iso3 = Column(String(3), nullable=True)
    survey_series = Column(String(100), nullable=True)
    year = Column(Integer, nullable=True)

    row_count = Column(Integer, nullable=True)
    column_count = Column(Integer, nullable=True)
    missing_cells = Column(Integer, nullable=True)

    access_status = Column(Enum(MicrodataAccessStatus), nullable=False, default=MicrodataAccessStatus.USER_UPLOAD)
    uploaded_by = Column(Uuid(as_uuid=True), ForeignKey("users.id"), nullable=False)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    project = relationship("MicrodataProject", back_populates="datasets")
    uploader = relationship("User", foreign_keys=[uploaded_by])
    variables = relationship("MicrodataVariable", back_populates="dataset", cascade="all, delete-orphan")
    jobs = relationship("MicrodataAnalysisJob", back_populates="dataset", cascade="all, delete-orphan")
    mappings = relationship("VariableMapping", back_populates="dataset", cascade="all, delete-orphan")

    __table_args__ = (
        Index("ix_microdata_datasets_country", "country_iso3"),
        Index("ix_microdata_datasets_uploaded_by", "uploaded_by"),
    )


class MicrodataVariable(Base):
    __tablename__ = "microdata_variables"

    id = Column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    dataset_id = Column(Uuid(as_uuid=True), ForeignKey("microdata_datasets.id"), nullable=False)

    variable_name = Column(String(255), nullable=False)
    variable_label = Column(Text, nullable=True)
    value_labels = Column(JSON, nullable=True)
    variable_index = Column(Integer, nullable=True)
    inferred_dtype = Column(String(50), nullable=True)
    missing_count = Column(Integer, nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())

    dataset = relationship("MicrodataDataset", back_populates="variables")

    __table_args__ = (
        Index("ix_microdata_variables_dataset", "dataset_id"),
    )


class VariableMapping(Base):
    """Maps one raw survey column to a canonical StandardConcept for a dataset.
    One standard concept maps to at most one raw variable per dataset (e.g. a
    dataset has exactly one "welfare" column), enforced by the unique index."""
    __tablename__ = "variable_mappings"

    id = Column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    dataset_id = Column(Uuid(as_uuid=True), ForeignKey("microdata_datasets.id"), nullable=False)

    standard_concept = Column(Enum(StandardConcept), nullable=False)
    raw_variable_name = Column(String(255), nullable=False)
    confidence = Column(Integer, nullable=True)  # 0-100, null when manually set/confirmed
    auto_detected = Column(Boolean, nullable=False, default=False)

    created_by = Column(Uuid(as_uuid=True), ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    dataset = relationship("MicrodataDataset", back_populates="mappings")

    __table_args__ = (
        Index("ix_variable_mappings_dataset", "dataset_id"),
        Index("ix_variable_mappings_dataset_concept", "dataset_id", "standard_concept", unique=True),
    )


class MicrodataAnalysisJob(Base):
    __tablename__ = "microdata_analysis_jobs"

    id = Column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    dataset_id = Column(Uuid(as_uuid=True), ForeignKey("microdata_datasets.id"), nullable=False)
    job_type = Column(Enum(MicrodataJobType), nullable=False)
    status = Column(Enum(MicrodataJobStatus), nullable=False, default=MicrodataJobStatus.PENDING)

    parameters = Column(JSON, nullable=True)
    error_message = Column(Text, nullable=True)

    requested_by = Column(Uuid(as_uuid=True), ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    completed_at = Column(DateTime(timezone=True), nullable=True)

    dataset = relationship("MicrodataDataset", back_populates="jobs")
    requester = relationship("User", foreign_keys=[requested_by])
    result = relationship("MicrodataAnalysisResult", back_populates="job", uselist=False, cascade="all, delete-orphan")


class MicrodataAnalysisResult(Base):
    __tablename__ = "microdata_analysis_results"

    id = Column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    job_id = Column(Uuid(as_uuid=True), ForeignKey("microdata_analysis_jobs.id"), nullable=False)

    summary_stats = Column(JSON, nullable=True)
    tables = Column(JSON, nullable=True)
    charts = Column(JSON, nullable=True)
    geojson = Column(JSON, nullable=True)
    interpretation_text = Column(Text, nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())

    job = relationship("MicrodataAnalysisJob", back_populates="result")


class ExplorerLayer(str, enum.Enum):
    """Which analytical layer an interactive spatial-explorer session is
    currently rendering on the map."""
    POVERTY = "poverty"
    AGRICULTURE = "agriculture"
    DIVERSIFICATION = "diversification"


class MicrodataExplorerSession(Base):
    """A saved, replayable interactive spatial-exploration session.

    Persists everything needed to reconstruct an exploration: which dataset
    and admin boundaries are loaded, which analytical layer (poverty /
    agriculture / diversification) is active, the row filters applied, the
    per-layer variable selections, and the map view. Running the session
    delegates to the same spatial analysis services the one-shot
    /analyze/spatial-* endpoints use, so no raw microdata is ever exposed —
    only aggregated, choropleth-ready GeoJSON."""
    __tablename__ = "microdata_explorer_sessions"

    id = Column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False, default="Untitled exploration")
    owner_id = Column(Uuid(as_uuid=True), ForeignKey("users.id"), nullable=False)
    dataset_id = Column(
        Uuid(as_uuid=True), ForeignKey("microdata_datasets.id", ondelete="SET NULL"), nullable=True
    )

    country_iso3 = Column(String(3), nullable=True)
    admin_level = Column(String(10), nullable=True)
    active_layer = Column(Enum(ExplorerLayer), nullable=False, default=ExplorerLayer.POVERTY)

    # Full replayable state: geo_variable, welfare_variable, poverty_line,
    # weight_variable, filters [{variable, op, value}], variable_overrides,
    # crop_columns / income_columns / livelihood_columns / livestock_columns,
    # map_view {center, zoom}, and last_job_ids per layer.
    state = Column(JSON, nullable=True)

    last_result_job_id = Column(
        Uuid(as_uuid=True), ForeignKey("microdata_analysis_jobs.id", ondelete="SET NULL"), nullable=True
    )

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    owner = relationship("User", foreign_keys=[owner_id])
    dataset = relationship("MicrodataDataset", foreign_keys=[dataset_id])

    __table_args__ = (
        Index("ix_microdata_explorer_sessions_owner", "owner_id"),
    )
