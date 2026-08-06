"""Ingestion must tolerate odd records and must not scale queries per record.

Two separate production failures are pinned here:

1. Catalogue-style connectors (DOI indexes, survey/microdata listings) emit
   records with no country_iso3 - or no mapping at all. A single AttributeError
   on those aborted a whole source's ingestion, which made the nightly refresh
   job exit non-zero and report a failed run.

2. Lookups used to run one SELECT per record. With ~40k records and the database
   in us-central1 while the refresh job runs in africa-south1, those round trips
   alone exceeded the job's task timeout, so it died before reaching the commit
   and every fetched record was thrown away.
"""
from app.services.ingestion_service import ingest_records


class _CountingSession:
    """Stand-in DB session that counts queries and captures bulk writes."""

    def __init__(self) -> None:
        self.committed = False
        self.queries = 0
        self.written: list = []

    def query(self, *args, **kwargs):
        self.queries += 1
        return self

    def filter(self, *args, **kwargs):
        return self

    def all(self):
        return []

    def first(self):
        return None

    def bulk_insert_mappings(self, _model, mappings):
        self.written.extend(mappings)

    def bulk_update_mappings(self, _model, mappings):
        self.written.extend(mappings)

    def commit(self) -> None:
        self.committed = True


def test_records_with_null_country_are_skipped_not_raised():
    records = [
        {"country_iso3": None, "indicator_code": "X", "year": 2020, "value": 1.0},
        {"indicator_code": "X", "year": 2020, "value": 1.0},  # key absent entirely
        {"country_iso3": "RWA", "indicator_code": None, "year": 2020, "value": 1.0},
    ]
    session = _CountingSession()
    assert ingest_records(session, "some_catalogue_source", records) == 0
    assert session.written == []


def test_non_mapping_records_are_skipped():
    records = ["10.1234/doi", None, 42, ["not", "a", "dict"]]
    session = _CountingSession()
    assert ingest_records(session, "doi_index", records) == 0
    assert session.written == []


def test_empty_record_list_short_circuits():
    assert ingest_records(_CountingSession(), "anything", []) == 0


def test_query_count_does_not_grow_with_record_count():
    """The regression that mattered: lookups must be bulk, not per record."""

    def run(n_years: int) -> int:
        session = _CountingSession()
        records = [
            {"country_iso3": "RWA", "indicator_code": "X", "year": y, "value": 1.0}
            for y in range(2000, 2000 + n_years)
        ]
        ingest_records(session, "world_bank", records)
        return session.queries

    small, large = run(5), run(500)
    assert small == large, (
        f"query count scaled with records ({small} -> {large}); "
        "the pre-load must stay a single bulk query"
    )
