"""Semantic search router — /api/v1/search"""

from __future__ import annotations

from typing import List

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.database import get_db
from app.services import search_service

router = APIRouter(prefix="/search", tags=["Search"])


class SearchResult(BaseModel):
    dataset_id: str
    title: str
    description: str
    score: float
    source_id: str
    tags: List[str]
    record_count: int


@router.get("/semantic", response_model=List[SearchResult])
def semantic_search(
    q: str = Query(..., description="Natural language search query"),
    limit: int = Query(10, ge=1, le=50),
    db: Session = Depends(get_db),
):
    return search_service.semantic_search(q, db, limit)
