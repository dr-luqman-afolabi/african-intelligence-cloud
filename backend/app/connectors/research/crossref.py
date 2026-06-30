"""Crossref connector — https://api.crossref.org (CC0, polite pool)."""
from __future__ import annotations

import time
from typing import Optional

import httpx

from app.connectors.research.base import (
    CitationRecord, HealthStatus, PaperMetadata, ResearchConnectorBase,
)

_BASE = "https://api.crossref.org"
_EMAIL = "research@african-intelligence-cloud.org"


class CrossrefConnector(ResearchConnectorBase):
    source_id = "crossref"

    def _get(self, path: str, params: dict | None = None) -> dict:
        resp = httpx.get(
            f"{_BASE}{path}",
            params=params or {},
            headers={"User-Agent": f"AIC/1.0 (mailto:{_EMAIL})"},
            timeout=15.0,
        )
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
        params: dict = {"query": query, "rows": min(max_results, 1000)}
        filters = []
        if year_from:
            filters.append(f"from-pub-date:{year_from}")
        if year_to:
            filters.append(f"until-pub-date:{year_to}")
        if filters:
            params["filter"] = ",".join(filters)
        data = self._get("/works", params)
        return [self._parse_item(item) for item in data.get("message", {}).get("items", [])]

    def get_metadata(self, external_id: str) -> Optional[PaperMetadata]:
        try:
            data = self._get(f"/works/{external_id}")
            return self._parse_item(data.get("message", {}))
        except Exception:
            return None

    def get_citations(self, external_id: str) -> list[CitationRecord]:
        try:
            data = self._get(f"/works/{external_id}")
            refs = data.get("message", {}).get("reference", [])
            return [
                CitationRecord(
                    cited_doi=r.get("DOI"),
                    cited_title=r.get("article-title"),
                    cited_year=int(r["year"]) if r.get("year") else None,
                )
                for r in refs
            ]
        except Exception:
            return []

    def get_abstract(self, external_id: str) -> Optional[str]:
        meta = self.get_metadata(external_id)
        return meta.abstract if meta else None

    def get_open_access_url(self, doi: str) -> Optional[str]:
        try:
            data = self._get(f"/works/{doi}")
            links = data.get("message", {}).get("link", [])
            for lnk in links:
                if lnk.get("content-type") == "application/pdf":
                    return lnk.get("URL")
            return None
        except Exception:
            return None

    def sync_metadata(self, query: str, max_results: int = 100) -> list[PaperMetadata]:
        return self.search_papers(query, max_results=max_results)

    def health_check(self) -> HealthStatus:
        t0 = time.monotonic()
        try:
            self._get("/works", {"rows": 1})
            latency = (time.monotonic() - t0) * 1000
            return HealthStatus(source_id=self.source_id, reachable=True, latency_ms=latency)
        except Exception as exc:
            return HealthStatus(source_id=self.source_id, reachable=False, latency_ms=None, message=str(exc))

    @staticmethod
    def _parse_item(item: dict) -> PaperMetadata:
        title = (item.get("title") or [""])[0]
        journal_list = item.get("container-title") or []
        journal = journal_list[0] if journal_list else None
        year = None
        published = item.get("published") or item.get("published-print") or item.get("published-online")
        if published:
            parts = published.get("date-parts", [[]])[0]
            if parts:
                year = parts[0]
        authors = [
            f"{a.get('given', '')} {a.get('family', '')}".strip()
            for a in item.get("author", [])
        ]
        abstract = item.get("abstract")
        if abstract:
            import re
            abstract = re.sub(r"<[^>]+>", "", abstract).strip()
        return PaperMetadata(
            external_id=item.get("DOI", ""),
            title=title,
            abstract=abstract,
            doi=item.get("DOI"),
            published_year=year,
            journal=journal,
            authors=authors,
            topics=item.get("subject", []),
            is_open_access=False,
            citation_count=item.get("is-referenced-by-count", 0),
            source_id="crossref",
        )
