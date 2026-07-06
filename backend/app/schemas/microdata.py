from __future__ import annotations

from typing import Optional, Any
from uuid import UUID
from datetime import datetime

from pydantic import BaseModel

from app.models.microdata import (
    MicrodataAccessStatus,
    MicrodataFileType,
    MicrodataJobStatus,
    MicrodataJobType,
)


class MicrodataDatasetResponse(BaseModel):
    id: UUID
    project_id: Optional[UUID] = None
    name: str
    original_filename: str
    file_type: MicrodataFileType
    file_size_bytes: Optional[int] = None
    country_iso3: Optional[str] = None
    survey_series: Optional[str] = None
    year: Optional[int] = None
    row_count: Optional[int] = None
    column_count: Optional[int] = None
    missing_cells: Optional[int] = None
    access_status: MicrodataAccessStatus
    uploaded_by: UUID
    created_at: datetime

    class Config:
        from_attributes = True


class MicrodataVariableResponse(BaseModel):
    id: UUID
    variable_name: str
    variable_label: Optional[str] = None
    value_labels: Optional[dict] = None
    variable_index: Optional[int] = None
    inferred_dtype: Optional[str] = None
    missing_count: Optional[int] = None

    class Config:
        from_attributes = True


class MicrodataDatasetListResponse(BaseModel):
    items: list[MicrodataDatasetResponse]
    total: int


class PovertyAnalysisRequest(BaseModel):
    dataset_id: UUID
    welfare_variable: str
    poverty_line: float
    weight_variable: Optional[str] = None
    group_by: Optional[list[str]] = None
    geography_variable: Optional[str] = None


class SpatialPovertyAnalysisRequest(BaseModel):
    dataset_id: UUID
    geo_variable: str
    welfare_variable: str
    poverty_line: float
    weight_variable: Optional[str] = None
    geojson_boundary_file: Optional[str] = None


class AnalysisResultResponse(BaseModel):
    job_id: UUID
    status: MicrodataJobStatus
    job_type: MicrodataJobType
    summary_stats: Optional[dict[str, Any]] = None
    tables: Optional[dict[str, Any]] = None
    charts: Optional[dict[str, Any]] = None
    geojson: Optional[dict[str, Any]] = None
    interpretation_text: Optional[str] = None
    error_message: Optional[str] = None
