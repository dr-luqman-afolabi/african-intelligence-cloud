"""Semantic Scholar connector — https://api.semanticscholar.org (open, no key required)."""
from __future__ import annotations

import time
from typing import Optional

import httpx

from app.connectors.research.base import (
    CitationRecord, HealthStatus, PaperMetadata, ResearchConnectorBase,
)

_BASE = "https://api.semanticscholar.org/graph/v1"
_FIELDS = "paperId,externalIds,title,abstract,year,venue,authors,topics,openAccessPdf,citationCount,isOpenAccess"


class SemanticScholarConnector(ResearchConnectorBase):
    source_id = "semantic_scholar"

    def _get(self, path: str, params: dict | None = None) -> dict:
        resp = httpx.get(f"{_BASE}{path}", params=params or {}, timeout=15.0)
        resp.raise_for_status()
        return resp.json()

    def search_papers(
        self,
        query: str,
        *,
        max_results: int = 20,
        year_from: Optional[int] = None,
        year_to: Optional[int] = None,
    ) -> list[PaperMetadata]:
        params: dict = {"query": query, "limit": min(max_results, 100), "fields": _FIELDS}
        if year_from or year_to:
            lo = year_from or 1900
            hi = year_to or 2100
            params["year"] = f"{lo}-{hi}"
        data = self._get("/paper/search", params)
        return [self._parse(p) for p in data.get("data", [])]

    def get_metadata(self, external_id: str) -> Optional[PaperMetadata]:
        try:
            paper = self._get(f"/paper/{external_id}", {"fields": _FIELDS})
            return self._parse(paper)
        except Exception:
            return None

    def get_citations(self, external_id: str) -> list[CitationRecord]:
        try:
            data = self._get(
                f"/paper/{external_id}/references",
                {"fields": "externalIds,title,year", "limit": 100},
            )
            return [
                CitationRecord(
                    cited_doi=(r.get("citedPaper", {}).get("externalIds") or {}).get("DOI"),
                    cited_title=r.get("citedPaper", {}).get("title"),
                    cited_year=r.get("citedPaper", {}).get("year"),
                )
                for r in data.get("data", [])
            ]
        except Exception:
            return []

    def get_abstract(self, external_id: str) -> Optional[str]:
        meta = self.get_metadata(external_id)
        return meta.abstract if meta else None

    def get_open_access_url(self, doi: str) -> Optional[str]:
        meta = self.get_metadata(f"DOI:{doi}")
        return meta.open_access_url if meta else None

    def sync_metadata(self, query: str, max_results: int = 100) -> list[PaperMetadata]:
        return self.search_papers(query, max_results=max_results)

    def health_check(self) -> HealthStatus:
        t0 = time.monotonic()
        try:
            self._get("/paper/search", {"query": "africa", "limit": 1, "fields": "paperId"})
            latency = (time.monotonic() - t0) * 1000
            return HealthStatus(source_id=self.source_id, reachable=True, latency_ms=latency)
        except Exception as exc:
            return HealthStatus(source_id=self.source_id, reachable=False, latency_ms=None, message=str(exc))

    @staticmethod
    def _parse(paper: dict) -> PaperMetadata:
        ext = paper.get("externalIds") or {}
        oa_pdf = paper.get("openAccessPdf") or {}
        return PaperMetadata(
            external_id=paper.get("paperId", ""),
            title=paper.get("title") or "",
            abstract=paper.get("abstract"),
            doi=ext.get("DOI"),
            published_year=paper.get("year"),
            journal=paper.get("venue"),
            authors=[a.get("name", "") for a in paper.get("authors", [])],
            topics=[t.get("topic", {}).get("name", "") for t in paper.get("topics", [])],
            open_access_url=oa_pdf.get("url"),
            is_open_access=paper.get("isOpenAccess", False),
            citation_count=paper.get("citationCount", 0),
            source_id="semantic_scholar",
        )
