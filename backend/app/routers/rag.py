"""RAG (Retrieval-Augmented Generation) router — /api/v1/rag"""

from __future__ import annotations

from typing import List, Optional

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.database import get_db
from app.services import rag_service

router = APIRouter(prefix="/rag", tags=["RAG"])


class ChatMessage(BaseModel):
    role: str  # "user" | "assistant"
    content: str


class RAGQueryRequest(BaseModel):
    query: str
    history: Optional[List[ChatMessage]] = []


class RAGSource(BaseModel):
    source_id: str
    title: str
    score: float
    excerpt: str


class RAGQueryResponse(BaseModel):
    answer: str
    sources: List[RAGSource]
    query_id: str


@router.post("/query", response_model=RAGQueryResponse)
def rag_query(req: RAGQueryRequest, db: Session = Depends(get_db)):
    result = rag_service.answer_query(req.query, db)
    return result
