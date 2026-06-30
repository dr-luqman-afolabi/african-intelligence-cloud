"""World Bank Documents connector — https://documents.worldbank.org (CC BY 4.0)."""
from __future__ import annotations

import time
from typing import Optional

import httpx

from app.connectors.research.base import (
    CitationRecord, HealthStatus, PaperMetadata, ResearchConnectorBase,
)

_BASE = "https://search.worldbank.org/api/v2/wds"


class WorldBankDocsConnector(ResearchConnectorBase):
    source_id = "worldbank_docs"

    def _get(self, params: dict | None = None) -> dict:
        resp = httpx.get(_BASE, params={**(params or {}), "format": "json"}, timeout=20.0)
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
        params: dict = {"qterm": query, "rows": min(max_results, 200), "fl": "all"}
        if year_from:
            params["datefrom"] = f"{year_from}-01-01"
        if year_to:
            params["dateto"] = f"{year_to}-12-31"
        data = self._get(params)
        docs = data.get("documents", {})
        return [self._parse(v) for k, v in docs.items() if isinstance(v, dict)]

    def get_metadata(self, external_id: str) -> Optional[PaperMetadata]:
        try:
            data = self._get({"id": external_id})
            docs = data.get("documents", {})
            for v in docs.values():
                if isinstance(v, dict):
                    return self._parse(v)
        except Exception:
            pass
        return None

    def get_citations(self, external_id: str) -> list[CitationRecord]:
        return []

    def get_abstract(self, external_id: str) -> Optional[str]:
        meta = self.get_metadata(external_id)
        return meta.abstract if meta else None

    def get_open_access_url(self, doi: str) -> Optional[str]:
        return None

    def sync_metadata(self, query: str, max_results: int = 100) -> list[PaperMetadata]:
        return self.search_papers(query, max_results=max_results)

    def health_check(self) -> HealthStatus:
        t0 = time.monotonic()
        try:
            self._get({"qterm": "africa", "rows": 1})
            latency = (time.monotonic() - t0) * 1000
            return HealthStatus(source_id=self.source_id, reachable=True, latency_ms=latency)
        except Exception as exc:
            return HealthStatus(source_id=self.source_id, reachable=False, latency_ms=None, message=str(exc))

    @staticmethod
    def _parse(doc: dict) -> PaperMetadata:
        year = None
        display_date = doc.get("displaydate") or doc.get("pdfurl", "")[:4]
        if display_date and display_date[:4].isdigit():
            year = int(display_date[:4])
        authors = [doc["authorname"]] if doc.get("authorname") else []
        return PaperMetadata(
            external_id=doc.get("id", ""),
            title=doc.get("display_title") or doc.get("docdt") or "",
            abstract=doc.get("abstract"),
            doi=doc.get("doi"),
            published_year=year,
            journal=doc.get("colti"),
            authors=authors,
            topics=doc.get("majdocty", "").split(",") if doc.get("majdocty") else [],
            open_access_url=doc.get("pdfurl"),
            is_open_access=bool(doc.get("pdfurl")),
            citation_count=0,
            source_id="worldbank_docs",
        )
