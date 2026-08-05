"""Ingestion must tolerate records that aren't country-indicator series.

Catalogue-style connectors (DOI indexes, survey/microdata listings) legitimately
emit records with no country_iso3 — or no mapping at all. Those have nothing to
contribute to macro_data, but they must be skipped rather than raising: a single
AttributeError here used to abort a whole source's ingestion, which in turn made
the nightly refresh job exit non-zero and report a failed run.
"""
from app.services.ingestion_service import ingest_records


class _NoQuerySession:
    """Stand-in DB session; ingesting only unusable records must never query."""

    def __init__(self) -> None:
        self.committed = False

    def query(self, *args, **kwargs):  # pragma: no cover - must not be reached
        raise AssertionError("ingest_records should skip unusable records before querying")

    def commit(self) -> None:
        self.committed = True


def test_records_with_null_country_are_skipped_not_raised():
    records = [
        {"country_iso3": None, "indicator_code": "X", "year": 2020, "value": 1.0},
        {"indicator_code": "X", "year": 2020, "value": 1.0},  # key absent entirely
        {"country_iso3": "RWA", "indicator_code": None, "year": 2020, "value": 1.0},
    ]
    assert ingest_records(_NoQuerySession(), "some_catalogue_source", records) == 0


def test_non_mapping_records_are_skipped():
    records = ["10.1234/doi", None, 42, ["not", "a", "dict"]]
    assert ingest_records(_NoQuerySession(), "doi_index", records) == 0


def test_empty_record_list_short_circuits():
    assert ingest_records(_NoQuerySession(), "anything", []) == 0
