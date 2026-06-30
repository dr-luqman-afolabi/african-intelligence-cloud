"""OpenAlex connector — https://api.openalex.org (CC0, no key required)."""
from __future__ import annotations

import time
from typing import Optional

import httpx

from app.connectors.research.base import (
    CitationRecord, HealthStatus, PaperMetadata, ResearchConnectorBase,
)

_BASE = "https://api.openalex.org"
_EMAIL = "research@african-intelligence-cloud.org"  # polite pool header


class OpenAlexConnector(ResearchConnectorBase):
    source_id = "openalex"

    def _get(self, path: str, params: dict | None = None, timeout: float = 10.0):
        headers = {"User-Agent": f"AIC/1.0 (mailto:{_EMAIL})"}
        resp = httpx.get(f"{_BASE}{path}", params=params or {}, headers=headers, timeout=timeout)
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
        params: dict = {
            "search": query,
            "per-page": min(max_results, 200),
            "select": "id,doi,title,abstract_inverted_index,publication_year,"
                      "primary_location,authorships,concepts,open_access,cited_by_count",
        }
        if year_from or year_to:
            lo = year_from or 1900
            hi = year_to or 2100
            params["filter"] = f"publication_year:{lo}-{hi}"

        data = self._get("/works", params)
        results = []
        for work in data.get("results", []):
            results.append(self._parse_work(work))
        return results

    def get_metadata(self, external_id: str) -> Optional[PaperMetadata]:
        try:
            work = self._get(f"/works/{external_id}")
            return self._parse_work(work)
        except Exception:
            return None

    def get_citations(self, external_id: str) -> list[CitationRecord]:
        try:
            data = self._get("/works", {"filter": f"cites:{external_id}", "per-page": 50})
            return [
                CitationRecord(
                    cited_doi=w.get("doi"),
                    cited_title=w.get("title"),
                    cited_year=w.get("publication_year"),
                )
                for w in data.get("results", [])
            ]
        except Exception:
            return []

    def get_abstract(self, external_id: str) -> Optional[str]:
        meta = self.get_metadata(external_id)
        return meta.abstract if meta else None

    def get_open_access_url(self, doi: str) -> Optional[str]:
        try:
            work = self._get(f"/works/https://doi.org/{doi}")
            oa = work.get("open_access", {})
            return oa.get("oa_url")
        except Exception:
            return None

    def sync_metadata(self, query: str, max_results: int = 100) -> list[PaperMetadata]:
        return self.search_papers(query, max_results=max_results)

    def health_check(self) -> HealthStatus:
        t0 = time.monotonic()
        try:
            self._get("/works", {"per-page": 1})
            latency = (time.monotonic() - t0) * 1000
            return HealthStatus(source_id=self.source_id, reachable=True, latency_ms=latency)
        except Exception as exc:
            return HealthStatus(source_id=self.source_id, reachable=False, latency_ms=None, message=str(exc))

    # ------------------------------------------------------------------
    # helpers
    # ------------------------------------------------------------------
    @staticmethod
    def _reconstruct_abstract(inverted: dict | None) -> Optional[str]:
        if not inverted:
            return None
        tokens = [""] * (max(max(v) for v in inverted.values()) + 1)
        for word, positions in inverted.items():
            for pos in positions:
                tokens[pos] = word
        return " ".join(tokens)

    def _parse_work(self, work: dict) -> PaperMetadata:
        loc = work.get("primary_location") or {}
        journal = None
        if loc.get("source"):
            journal = loc["source"].get("display_name")
        oa = work.get("open_access") or {}
        return PaperMetadata(
            external_id=work.get("id", ""),
            title=work.get("title") or "",
            abstract=self._reconstruct_abstract(work.get("abstract_inverted_index")),
            doi=work.get("doi"),
            published_year=work.get("publication_year"),
            journal=journal,
            authors=[
                a.get("author", {}).get("display_name", "")
                for a in work.get("authorships", [])
            ],
            topics=[c.get("display_name", "") for c in work.get("concepts", [])],
            open_access_url=oa.get("oa_url"),
            is_open_access=oa.get("is_oa", False),
            citation_count=work.get("cited_by_count", 0),
            source_id=self.source_id,
        )
