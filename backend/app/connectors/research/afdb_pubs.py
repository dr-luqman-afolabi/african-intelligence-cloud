"""AfDB Publications connector — https://www.afdb.org (CC BY 3.0 IGO, OAI-PMH)."""
from __future__ import annotations

import time
import xml.etree.ElementTree as ET
from typing import Optional

import httpx

from app.connectors.research.base import (
    CitationRecord, HealthStatus, PaperMetadata, ResearchConnectorBase,
)

_OAI = "https://www.afdb.org/api/oai"
_SEARCH = "https://www.afdb.org/api/search"

_NS = {
    "oai": "http://www.openarchives.org/OAI/2.0/",
    "dc": "http://purl.org/dc/elements/1.1/",
    "oai_dc": "http://www.openarchives.org/OAI/2.0/oai_dc/",
}


class AfdbPubsConnector(ResearchConnectorBase):
    source_id = "afdb_pubs"

    def _oai_request(self, params: dict) -> ET.Element:
        resp = httpx.get(_OAI, params=params, timeout=20.0)
        resp.raise_for_status()
        return ET.fromstring(resp.text)

    def _search(self, query: str, limit: int = 20) -> list[dict]:
        try:
            resp = httpx.get(
                _SEARCH,
                params={"q": query, "language": "en", "rows": limit},
                timeout=20.0,
            )
            resp.raise_for_status()
            data = resp.json()
            return data.get("items", data.get("results", []))
        except Exception:
            return []

    def search_papers(
        self,
        query: str,
        *,
        max_results: int = 20,
        year_from: Optional[int] = None,
        year_to: Optional[int] = None,
    ) -> list[PaperMetadata]:
        items = self._search(query, limit=max_results)
        papers = [self._parse_item(i) for i in items]
        if year_from or year_to:
            papers = [
                p for p in papers
                if p.published_year is not None
                and (year_from is None or p.published_year >= year_from)
                and (year_to is None or p.published_year <= year_to)
            ]
        return papers

    def get_metadata(self, external_id: str) -> Optional[PaperMetadata]:
        try:
            root = self._oai_request({"verb": "GetRecord", "identifier": external_id, "metadataPrefix": "oai_dc"})
            record = root.find(".//oai:record", _NS)
            if record is not None:
                return self._parse_oai_record(record)
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
        results = []
        try:
            params = {"verb": "ListRecords", "metadataPrefix": "oai_dc", "set": "publications"}
            root = self._oai_request(params)
            for record in root.findall(".//oai:record", _NS):
                results.append(self._parse_oai_record(record))
                if len(results) >= max_results:
                    break
        except Exception:
            results = self.search_papers(query, max_results=max_results)
        return results

    def health_check(self) -> HealthStatus:
        t0 = time.monotonic()
        try:
            self._oai_request({"verb": "Identify"})
            latency = (time.monotonic() - t0) * 1000
            return HealthStatus(source_id=self.source_id, reachable=True, latency_ms=latency)
        except Exception as exc:
            return HealthStatus(source_id=self.source_id, reachable=False, latency_ms=None, message=str(exc))

    def _parse_item(self, item: dict) -> PaperMetadata:
        year = None
        raw_date = item.get("date") or item.get("year") or ""
        if raw_date and str(raw_date)[:4].isdigit():
            year = int(str(raw_date)[:4])
        return PaperMetadata(
            external_id=str(item.get("id", "")),
            title=item.get("title", ""),
            abstract=item.get("description") or item.get("abstract"),
            doi=item.get("doi"),
            published_year=year,
            journal=item.get("series") or item.get("collection"),
            authors=item.get("authors", []) if isinstance(item.get("authors"), list) else [],
            topics=item.get("topics", []) if isinstance(item.get("topics"), list) else [],
            open_access_url=item.get("url") or item.get("pdf_url"),
            is_open_access=True,
            citation_count=0,
            source_id=self.source_id,
        )

    def _parse_oai_record(self, record: ET.Element) -> PaperMetadata:
        dc = record.find(".//oai_dc:dc", _NS)
        if dc is None:
            return PaperMetadata(external_id="", title="", source_id=self.source_id)

        def _text(tag: str) -> Optional[str]:
            el = dc.find(f"dc:{tag}", _NS)
            return el.text.strip() if el is not None and el.text else None

        def _all(tag: str) -> list[str]:
            return [el.text.strip() for el in dc.findall(f"dc:{tag}", _NS) if el.text]

        ident = record.find(".//oai:identifier", _NS)
        year = None
        raw = _text("date") or ""
        if raw[:4].isdigit():
            year = int(raw[:4])

        return PaperMetadata(
            external_id=ident.text.strip() if ident is not None and ident.text else "",
            title=_text("title") or "",
            abstract=_text("description"),
            doi=None,
            published_year=year,
            journal=_text("source"),
            authors=_all("creator"),
            topics=_all("subject"),
            open_access_url=_text("identifier"),
            is_open_access=True,
            citation_count=0,
            source_id=self.source_id,
        )
