"""DOAJ connector — https://doaj.org/api (CC BY-SA, open)."""
from __future__ import annotations

import time
from typing import Optional

import httpx

from app.connectors.research.base import (
    CitationRecord, HealthStatus, PaperMetadata, ResearchConnectorBase,
)

_BASE = "https://doaj.org/api"


class DoajConnector(ResearchConnectorBase):
    source_id = "doaj"

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
        q = query
        if year_from:
            q += f" AND year:[{year_from} TO {year_to or 2100}]"
        params = {"q": q, "pageSize": min(max_results, 100), "page": 1}
        data = self._get("/search/articles", params)
        return [self._parse(r) for r in data.get("results", [])]

    def get_metadata(self, external_id: str) -> Optional[PaperMetadata]:
        try:
            data = self._get(f"/articles/{external_id}")
            return self._parse(data)
        except Exception:
            return None

    def get_citations(self, external_id: str) -> list[CitationRecord]:
        return []

    def get_abstract(self, external_id: str) -> Optional[str]:
        meta = self.get_metadata(external_id)
        return meta.abstract if meta else None

    def get_open_access_url(self, doi: str) -> Optional[str]:
        try:
            data = self._get("/search/articles", {"q": f"doi:{doi}", "pageSize": 1})
            results = data.get("results", [])
            if results:
                return results[0].get("bibjson", {}).get("link", [{}])[0].get("url")
        except Exception:
            pass
        return None

    def sync_metadata(self, query: str, max_results: int = 100) -> list[PaperMetadata]:
        return self.search_papers(query, max_results=max_results)

    def health_check(self) -> HealthStatus:
        t0 = time.monotonic()
        try:
            self._get("/search/articles", {"q": "africa", "pageSize": 1})
            latency = (time.monotonic() - t0) * 1000
            return HealthStatus(source_id=self.source_id, reachable=True, latency_ms=latency)
        except Exception as exc:
            return HealthStatus(source_id=self.source_id, reachable=False, latency_ms=None, message=str(exc))

    @staticmethod
    def _parse(result: dict) -> PaperMetadata:
        bib = result.get("bibjson", {})
        identifiers = {i["type"]: i["id"] for i in bib.get("identifier", [])}
        links = bib.get("link", [])
        oa_url = links[0].get("url") if links else None
        year = bib.get("year")
        return PaperMetadata(
            external_id=result.get("id", ""),
            title=bib.get("title", ""),
            abstract=bib.get("abstract"),
            doi=identifiers.get("doi"),
            published_year=int(year) if year else None,
            journal=bib.get("journal", {}).get("title"),
            authors=[
                f"{a.get('name', '')}".strip()
                for a in bib.get("author", [])
            ],
            topics=[s.get("term", "") for s in bib.get("subject", [])],
            open_access_url=oa_url,
            is_open_access=True,
            citation_count=0,
            source_id="doaj",
        )
