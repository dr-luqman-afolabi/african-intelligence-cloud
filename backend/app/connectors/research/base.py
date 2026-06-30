"""Abstract base class for all open research source connectors."""
from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class PaperMetadata:
    external_id: str
    title: str
    abstract: Optional[str] = None
    doi: Optional[str] = None
    published_year: Optional[int] = None
    journal: Optional[str] = None
    authors: list[str] = field(default_factory=list)
    topics: list[str] = field(default_factory=list)
    open_access_url: Optional[str] = None
    is_open_access: bool = False
    citation_count: int = 0
    source_id: str = ""


@dataclass
class CitationRecord:
    cited_doi: Optional[str]
    cited_title: Optional[str]
    cited_year: Optional[int]


@dataclass
class HealthStatus:
    source_id: str
    reachable: bool
    latency_ms: Optional[float]
    message: str = ""


class ResearchConnectorBase(ABC):
    """Every research source connector must implement these methods."""

    source_id: str = ""

    @abstractmethod
    def search_papers(
        self,
        query: str,
        *,
        max_results: int = 20,
        year_from: Optional[int] = None,
        year_to: Optional[int] = None,
    ) -> list[PaperMetadata]:
        """Full-text or keyword search; returns ranked paper metadata."""

    @abstractmethod
    def get_metadata(self, external_id: str) -> Optional[PaperMetadata]:
        """Retrieve full metadata for a single paper by its source ID or DOI."""

    @abstractmethod
    def get_citations(self, external_id: str) -> list[CitationRecord]:
        """Return the reference list of a paper."""

    @abstractmethod
    def get_abstract(self, external_id: str) -> Optional[str]:
        """Return the abstract text for a paper."""

    @abstractmethod
    def get_open_access_url(self, doi: str) -> Optional[str]:
        """Return a direct open-access PDF/HTML URL for the given DOI, or None."""

    @abstractmethod
    def sync_metadata(self, query: str, max_results: int = 100) -> list[PaperMetadata]:
        """Bulk sync: search and return results for storage in the local DB."""

    @abstractmethod
    def health_check(self) -> HealthStatus:
        """Ping the source API and return reachability + latency."""
