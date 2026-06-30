from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any

logger = logging.getLogger(__name__)


@dataclass
class HealthStatus:
    source_id: str
    healthy: bool
    latency_ms: float | None = None
    message: str = ""
    checked_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


@dataclass
class ConnectorMetadata:
    source_id: str
    source_name: str
    description: str
    base_url: str
    license_category: str  # A | B | C | D
    update_frequency: str
    supported_indicators: list[str] = field(default_factory=list)
    supported_countries: list[str] = field(default_factory=list)


class BaseConnector(ABC):
    """
    Interface every AIC data connector must implement.

    Lifecycle: health_check → fetch → normalise → persist (via connector_service).
    """

    source_id: str = ""

    def get_metadata(self) -> ConnectorMetadata:
        """Return static metadata about this connector. Override in subclasses."""
        raise NotImplementedError(f"{self.__class__.__name__} must implement get_metadata()")

    @abstractmethod
    def health_check(self) -> HealthStatus:
        """Probe the upstream source. Must be fast (< 5 s)."""

    @abstractmethod
    def fetch(self, **kwargs: Any) -> list[dict]:
        """
        Pull raw records from the upstream source.

        Returns a list of dicts with source-specific keys.
        Raises ConnectorError on network or parse failure.
        """

    @abstractmethod
    def normalise(self, raw: list[dict]) -> list[dict]:
        """
        Transform raw records into AIC canonical schema:
          country_iso3, indicator_code, year, value, unit, data_source, source_id
        """

    def sync(self, **kwargs: Any) -> list[dict]:
        """
        Fetch → normalise. Returns normalised records.

        connector_service calls this and handles persistence.
        """
        raw = self.fetch(**kwargs)
        return self.normalise(raw)


class ConnectorError(Exception):
    """Raised when a connector cannot fetch or parse upstream data."""
