import uuid
import enum
from sqlalchemy import Column, String, Boolean, Integer, BigInteger, Numeric, ForeignKey, Enum, DateTime, JSON, Text, Uuid, Index
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base


class DatasetPrivacy(str, enum.Enum):
    PRIVATE = "private"
    ORGANIZATION = "organization"
    PUBLIC = "public"


class DatasetStatus(str, enum.Enum):
    UPLOADED = "uploaded"
    PROFILING = "profiling"
    PROFILED = "profiled"
    FAILED = "failed"


class UploadedDataset(Base):
    __tablename__ = "uploaded_datasets"

    id = Column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    original_filename = Column(String(500), nullable=False)
    file_extension = Column(String(20), nullable=False)
    file_size_bytes = Column(BigInteger, nullable=False)
    storage_path = Column(String(1000), nullable=False)
    privacy = Column(Enum(DatasetPrivacy), nullable=False, default=DatasetPrivacy.PRIVATE)
    status = Column(Enum(DatasetStatus), nullable=False, default=DatasetStatus.UPLOADED)
    row_count = Column(Integer, nullable=True)
    column_count = Column(Integer, nullable=True)
    tags = Column(JSON, nullable=True, default=list)

    uploaded_by = Column(Uuid(as_uuid=True), ForeignKey("users.id"), nullable=False)
    organization_id = Column(Uuid(as_uuid=True), ForeignKey("organizations.id"), nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    uploader = relationship("User", foreign_keys=[uploaded_by])
    organization = relationship("Organization")
    columns = relationship("DatasetColumn", back_populates="dataset", cascade="all, delete-orphan")
    profile = relationship("DatasetProfile", back_populates="dataset", uselist=False, cascade="all, delete-orphan")
    jobs = relationship("AnalysisJob", back_populates="dataset", cascade="all, delete-orphan")

    __table_args__ = (
        Index("ix_uploaded_datasets_org", "organization_id"),
        Index("ix_uploaded_datasets_uploader", "uploaded_by"),
        Index("ix_uploaded_datasets_status", "status"),
    )


class DatasetColumn(Base):
    __tablename__ = "dataset_columns"

    id = Column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    dataset_id = Column(Uuid(as_uuid=True), ForeignKey("uploaded_datasets.id", ondelete="CASCADE"), nullable=False)
    column_name = Column(String(500), nullable=False)
    column_index = Column(Integer, nullable=False)
    inferred_dtype = Column(String(100), nullable=True)
    null_count = Column(Integer, nullable=True, default=0)
    unique_count = Column(Integer, nullable=True)
    sample_values = Column(JSON, nullable=True)
    min_value = Column(String(255), nullable=True)
    max_value = Column(String(255), nullable=True)
    mean_value = Column(Numeric(20, 6), nullable=True)

    dataset = relationship("UploadedDataset", back_populates="columns")

    __table_args__ = (
        Index("ix_dataset_columns_dataset", "dataset_id"),
    )


class DatasetProfile(Base):
    __tablename__ = "dataset_profiles"

    id = Column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    dataset_id = Column(Uuid(as_uuid=True), ForeignKey("uploaded_datasets.id", ondelete="CASCADE"), nullable=False, unique=True)
    row_count = Column(Integer, nullable=False)
    column_count = Column(Integer, nullable=False)
    missing_cells = Column(Integer, nullable=False, default=0)
    missing_cells_pct = Column(Numeric(5, 2), nullable=False, default=0)
    duplicate_rows = Column(Integer, nullable=False, default=0)
    numeric_columns = Column(Integer, nullable=False, default=0)
    categorical_columns = Column(Integer, nullable=False, default=0)
    datetime_columns = Column(Integer, nullable=False, default=0)
    profiled_at = Column(DateTime(timezone=True), server_default=func.now())
    profiling_duration_ms = Column(Integer, nullable=True)
    error_message = Column(Text, nullable=True)

    dataset = relationship("UploadedDataset", back_populates="profile")


class AnalysisJob(Base):
    __tablename__ = "analysis_jobs"

    id = Column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    dataset_id = Column(Uuid(as_uuid=True), ForeignKey("uploaded_datasets.id", ondelete="CASCADE"), nullable=False)
    job_type = Column(String(100), nullable=False, default="profile")
    status = Column(String(50), nullable=False, default="queued")
    started_at = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    error_message = Column(Text, nullable=True)
    result_summary = Column(JSON, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    dataset = relationship("UploadedDataset", back_populates="jobs")

    __table_args__ = (
        Index("ix_analysis_jobs_dataset", "dataset_id"),
        Index("ix_analysis_jobs_status", "status"),
    )
