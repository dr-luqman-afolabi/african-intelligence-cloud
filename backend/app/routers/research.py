"""Research router — /api/v1/research (Tasks 5 + 6)."""
from __future__ import annotations

import uuid
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.research_paper import ResearchPaper
from app.services.research_source_service import list_sources, get_source
from app.services.research_service import (
    recommend_theories,
    recommend_variables,
    recommend_methods,
    generate_literature_matrix,
    identify_research_gaps,
    generate_conceptual_framework,
    generate_hypotheses,
    suggest_african_datasets,
)
from app.connectors.research.openalex import OpenAlexConnector
from app.connectors.research.crossref import CrossrefConnector
from app.connectors.research.semantic_scholar import SemanticScholarConnector

router = APIRouter(prefix="/research", tags=["Research"])

# ---------------------------------------------------------------------------
# Pydantic schemas
# ---------------------------------------------------------------------------


class LiteratureReviewRequest(BaseModel):
    topic: str
    year_from: Optional[int] = None
    year_to: Optional[int] = None
    max_results: int = 20
    source_ids: list[str] = []


class TheoryRequest(BaseModel):
    topic: str
    context: str = ""


class MethodRequest(BaseModel):
    topic: str
    context: str = ""


class VariableRequest(BaseModel):
    topic: str
    context: str = ""


class SyncRequest(BaseModel):
    source_id: str
    query: str
    max_results: int = 50


# ---------------------------------------------------------------------------
# Source registry endpoints
# ---------------------------------------------------------------------------


@router.get("/sources")
def get_sources(active_only: bool = True, db: Session = Depends(get_db)):
    """List all registered open research sources."""
    sources = list_sources(db, active_only=active_only)
    return [
        {
            "source_id": s.source_id,
            "name": s.name,
            "type": s.type,
            "api_url": s.api_url,
            "license": s.license,
            "african_relevance_score": s.african_relevance_score,
            "full_text_allowed": s.full_text_allowed,
            "rate_limit": s.rate_limit,
            "description": s.description,
        }
        for s in sources
    ]


# ---------------------------------------------------------------------------
# Search
# ---------------------------------------------------------------------------


@router.get("/search")
def search_papers(
    q: str,
    source: str = "openalex",
    max_results: int = 20,
    year_from: Optional[int] = None,
    year_to: Optional[int] = None,
):
    """Full-text paper search across open sources."""
    connector_map = {
        "openalex": OpenAlexConnector,
        "crossref": CrossrefConnector,
        "semantic_scholar": SemanticScholarConnector,
    }
    cls = connector_map.get(source)
    if cls is None:
        raise HTTPException(status_code=400, detail=f"Unsupported source: {source}")

    connector = cls()
    try:
        papers = connector.search_papers(q, max_results=max_results, year_from=year_from, year_to=year_to)
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Upstream error from {source}: {exc}") from exc

    return {
        "query": q,
        "source": source,
        "total": len(papers),
        "results": [
            {
                "external_id": p.external_id,
                "title": p.title,
                "abstract": p.abstract,
                "doi": p.doi,
                "published_year": p.published_year,
                "journal": p.journal,
                "authors": p.authors,
                "topics": p.topics,
                "open_access_url": p.open_access_url,
                "is_open_access": p.is_open_access,
                "citation_count": p.citation_count,
                "source_id": p.source_id,
            }
            for p in papers
        ],
    }


# ---------------------------------------------------------------------------
# Paper detail
# ---------------------------------------------------------------------------


@router.get("/paper/{paper_id}")
def get_paper(paper_id: str, db: Session = Depends(get_db)):
    """Get stored paper metadata by UUID or DOI."""
    paper: Optional[ResearchPaper] = None
    try:
        uid = uuid.UUID(paper_id)
        paper = db.query(ResearchPaper).filter(ResearchPaper.id == uid).first()
    except ValueError:
        paper = db.query(ResearchPaper).filter(ResearchPaper.doi == paper_id).first()

    if not paper:
        raise HTTPException(status_code=404, detail="Paper not found")

    return {
        "id": str(paper.id),
        "doi": paper.doi,
        "title": paper.title,
        "abstract": paper.abstract,
        "published_year": paper.published_year,
        "journal": paper.journal,
        "is_open_access": paper.is_open_access,
        "open_access_url": paper.open_access_url,
        "citation_count": paper.citation_count,
        "authors": [{"full_name": a.full_name, "affiliation": a.affiliation} for a in paper.authors],
        "topics": [t.topic for t in paper.topics],
        "methods": [m.method_name for m in paper.methods],
        "theories": [t.theory_name for t in paper.theories],
        "policy_areas": [p.policy_area for p in paper.policy_areas],
        "citations": [
            {"doi": c.cited_doi, "title": c.cited_title, "year": c.cited_year}
            for c in paper.citing_papers
        ],
    }


# ---------------------------------------------------------------------------
# Sync
# ---------------------------------------------------------------------------


@router.post("/sync")
def sync_papers(req: SyncRequest, background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    """Sync papers from an open source into the local database (async)."""
    source = get_source(db, req.source_id)
    if not source:
        raise HTTPException(status_code=404, detail=f"Source '{req.source_id}' not found")

    def _sync():
        connector_map = {
            "openalex": OpenAlexConnector,
            "crossref": CrossrefConnector,
            "semantic_scholar": SemanticScholarConnector,
        }
        cls = connector_map.get(req.source_id)
        if cls is None:
            return
        connector = cls()
        papers = connector.sync_metadata(req.query, max_results=req.max_results)
        with db:
            for p in papers:
                existing = db.query(ResearchPaper).filter(
                    ResearchPaper.external_id == p.external_id
                ).first()
                if not existing:
                    db.add(ResearchPaper(
                        id=uuid.uuid4(),
                        external_id=p.external_id,
                        doi=p.doi,
                        title=p.title,
                        abstract=p.abstract,
                        published_year=p.published_year,
                        journal=p.journal,
                        is_open_access=p.is_open_access,
                        open_access_url=p.open_access_url,
                        citation_count=p.citation_count,
                        source_id=source.id,
                    ))
            db.commit()

    background_tasks.add_task(_sync)
    return {"status": "sync_started", "source_id": req.source_id, "query": req.query}


# ---------------------------------------------------------------------------
# Literature review
# ---------------------------------------------------------------------------


@router.post("/literature-review")
def literature_review(req: LiteratureReviewRequest, db: Session = Depends(get_db)):
    """Search open sources and generate a literature review matrix."""
    connector = OpenAlexConnector()
    try:
        raw_papers = connector.search_papers(
            req.topic,
            max_results=req.max_results,
            year_from=req.year_from,
            year_to=req.year_to,
        )
    except Exception as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc

    matrix_rows = [
        {
            "title": p.title,
            "authors": p.authors,
            "year": p.published_year,
            "journal": p.journal,
            "doi": p.doi,
            "is_open_access": p.is_open_access,
            "citation_count": p.citation_count,
            "topics": p.topics,
            "theories_used": [],
            "methods_used": [],
        }
        for p in raw_papers
    ]

    gaps = identify_research_gaps(
        [{"topics": p.topics} for p in raw_papers], req.topic
    )
    theories = recommend_theories(req.topic)
    methods = recommend_methods(req.topic)

    return {
        "topic": req.topic,
        "total_papers": len(matrix_rows),
        "matrix": matrix_rows,
        "research_gaps": gaps,
        "recommended_theories": theories,
        "recommended_methods": methods,
    }


# ---------------------------------------------------------------------------
# Theory recommendation
# ---------------------------------------------------------------------------


@router.post("/theory-recommendation")
def theory_recommendation(req: TheoryRequest):
    theories = recommend_theories(req.topic, req.context)
    return {"topic": req.topic, "recommended_theories": theories}


# ---------------------------------------------------------------------------
# Method recommendation
# ---------------------------------------------------------------------------


@router.post("/method-recommendation")
def method_recommendation(req: MethodRequest):
    methods = recommend_methods(req.topic, req.context)
    return {"topic": req.topic, "recommended_methods": methods}


# ---------------------------------------------------------------------------
# Variable recommendation
# ---------------------------------------------------------------------------


@router.post("/variable-recommendation")
def variable_recommendation(req: VariableRequest):
    variables = recommend_variables(req.topic, req.context)
    datasets = suggest_african_datasets(req.topic)
    framework = generate_conceptual_framework(req.topic, [], [v["variable"] for v in variables])
    hypotheses = generate_hypotheses(req.topic, [], [v["variable"] for v in variables])
    return {
        "topic": req.topic,
        "recommended_variables": variables,
        "african_datasets": datasets,
        "conceptual_framework": framework,
        "hypotheses": hypotheses,
    }
