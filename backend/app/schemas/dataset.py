from pydantic import BaseModel, Field, field_validator
from typing import Optional, Any
from uuid import UUID
from datetime import datetime
from app.models.dataset import DatasetPrivacy, DatasetStatus


ALLOWED_EXTENSIONS = {"csv", "xlsx", "xls", "json", "parquet"}


class DatasetUploadResponse(BaseModel):
    id: UUID
    name: str
    original_filename: str
    file_extension: str
    file_size_bytes: int
    privacy: DatasetPrivacy
    status: DatasetStatus
    uploaded_by: UUID
    organization_id: Optional[UUID]
    created_at: datetime

    class Config:
        from_attributes = True


class DatasetColumnSchema(BaseModel):
    id: UUID
    column_name: str
    column_index: int
    inferred_dtype: Optional[str]
    null_count: Optional[int]
    unique_count: Optional[int]
    sample_values: Optional[list[Any]]
    min_value: Optional[str]
    max_value: Optional[str]
    mean_value: Optional[float]

    class Config:
        from_attributes = True


class DatasetProfileSchema(BaseModel):
    id: UUID
    row_count: int
    column_count: int
    missing_cells: int
    missing_cells_pct: float
    duplicate_rows: int
    numeric_columns: int
    categorical_columns: int
    datetime_columns: int
    profiled_at: datetime
    profiling_duration_ms: Optional[int]

    class Config:
        from_attributes = True


class DatasetDetailResponse(BaseModel):
    id: UUID
    name: str
    description: Optional[str]
    original_filename: str
    file_extension: str
    file_size_bytes: int
    privacy: DatasetPrivacy
    status: DatasetStatus
    row_count: Optional[int]
    column_count: Optional[int]
    tags: Optional[list[str]]
    uploaded_by: UUID
    organization_id: Optional[UUID]
    created_at: datetime
    updated_at: datetime
    columns: list[DatasetColumnSchema]
    profile: Optional[DatasetProfileSchema]

    class Config:
        from_attributes = True


class DatasetListItem(BaseModel):
    id: UUID
    name: str
    original_filename: str
    file_extension: str
    file_size_bytes: int
    privacy: DatasetPrivacy
    status: DatasetStatus
    row_count: Optional[int]
    column_count: Optional[int]
    tags: Optional[list[str]]
    uploaded_by: UUID
    organization_id: Optional[UUID]
    created_at: datetime

    class Config:
        from_attributes = True


class DatasetListResponse(BaseModel):
    items: list[DatasetListItem]
    total: int
    page: int
    page_size: int


class ProfileTriggerResponse(BaseModel):
    message: str
    dataset_id: UUID
    status: DatasetStatus
