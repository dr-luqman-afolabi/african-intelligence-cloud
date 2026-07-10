"""Schemas for AIC Intelligence — the conversational microdata analyst."""
from __future__ import annotations

from typing import Any, Optional
from uuid import UUID

from pydantic import BaseModel


class IntelligencePlanRequest(BaseModel):
    dataset_id: UUID
    question: str


class CleaningStep(BaseModel):
    kind: str
    label: str
    columns: Optional[list[str]] = None
    column: Optional[str] = None
    strategy: Optional[str] = None
    lower: Optional[float] = None
    upper: Optional[float] = None
    op: Optional[str] = None
    value: Optional[float] = None


class IntelligencePlan(BaseModel):
    analysis: str                       # e.g. "spatial-poverty"
    analysis_label: str
    endpoint: str                       # frontend API route to call on run
    parameters: dict[str, Any]          # mapped analysis params (minus dataset_id)
    cleaning_steps: list[CleaningStep]
    rationale: str
    warnings: list[str] = []
    engine: str                         # "gemini" | "heuristic"
    needs_clarification: bool = False
    clarification: Optional[str] = None


class IntelligenceCleanRequest(BaseModel):
    dataset_id: UUID
    question: Optional[str] = None
    cleaning_steps: Optional[list[CleaningStep]] = None
    target_columns: Optional[list[str]] = None


class IntelligenceCleanResponse(BaseModel):
    cleaned_dataset_id: UUID
    cleaned_dataset_name: str
    report: list[str]
    row_count: int
    column_count: int
