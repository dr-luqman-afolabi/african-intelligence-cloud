"""Tests for Sprint 8 — Open Research Intelligence."""
from __future__ import annotations

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from types import SimpleNamespace
from unittest.mock import patch, MagicMock

from app.main import app
from app.database import Base, get_db
from app.services.research_service import (
    recommend_theories,
    recommend_methods,
    recommend_variables,
    generate_literature_matrix,
    identify_research_gaps,
    generate_conceptual_framework,
    generate_hypotheses,
    suggest_african_datasets,
)
from app.services.export_service import export_bibtex, export_ris, export_csv, export_excel

# Dedicated, isolated in-memory DB so GET /research/sources doesn't depend on
# whichever other test file happened to run before this one and left the
# shared conftest engine's tables in place.
_engine = create_engine(
    "sqlite:///:memory:", connect_args={"check_same_thread": False}, poolclass=StaticPool
)
_TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=_engine)
Base.metadata.create_all(bind=_engine)


def _override_get_db():
    db = _TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


client = TestClient(app)


# ---------------------------------------------------------------------------
# AI service — recommend_theories
# ---------------------------------------------------------------------------
class TestRecommendTheories:
    def test_returns_list(self):
        result = recommend_theories("financial inclusion")
        assert isinstance(result, list)

    def test_each_item_has_required_keys(self):
        result = recommend_theories("poverty")
        for item in result:
            # Key is "name" (not "theory") — frontend's TheoryPanel.tsx reads t.name.
            assert "name" in item
            assert "relevance_score" in item
            assert "african_relevance" in item
            assert "description" in item

    def test_scores_are_floats_between_0_and_1(self):
        result = recommend_theories("economic growth")
        for item in result:
            assert 0.0 <= item["relevance_score"] <= 1.0
            assert 0.0 <= item["african_relevance"] <= 1.0

    def test_sorted_by_relevance_descending(self):
        result = recommend_theories("trade")
        if len(result) > 1:
            scores = [r["relevance_score"] for r in result]
            assert scores == sorted(scores, reverse=True)


# ---------------------------------------------------------------------------
# AI service — recommend_methods
# ---------------------------------------------------------------------------
class TestRecommendMethods:
    def test_returns_list(self):
        result = recommend_methods("education outcomes")
        assert isinstance(result, list)

    def test_each_item_has_required_keys(self):
        result = recommend_methods("panel data")
        for item in result:
            assert "method" in item
            assert "relevance_score" in item
            assert "description" in item
            assert "software" in item

    def test_software_is_list(self):
        result = recommend_methods("regression")
        for item in result:
            assert isinstance(item["software"], list)


# ---------------------------------------------------------------------------
# AI service — recommend_variables
# ---------------------------------------------------------------------------
class TestRecommendVariables:
    def test_returns_list(self):
        result = recommend_variables("governance")
        assert isinstance(result, list)

    def test_each_item_has_required_keys(self):
        result = recommend_variables("FDI")
        for item in result:
            assert "variable" in item
            assert "relevance_score" in item
            assert "recommended_sources" in item


# ---------------------------------------------------------------------------
# AI service — suggest_african_datasets
# ---------------------------------------------------------------------------
class TestSuggestAfricanDatasets:
    def test_returns_list(self):
        result = suggest_african_datasets("poverty")
        assert isinstance(result, list)

    def test_each_dataset_has_required_keys(self):
        result = suggest_african_datasets("health")
        for ds in result:
            assert "name" in ds
            assert "url" in ds
            assert "coverage" in ds


# ---------------------------------------------------------------------------
# AI service — generate_literature_matrix
# ---------------------------------------------------------------------------
def _make_paper(
    title="Paper", authors=(), published_year=2020, journal=None, doi=None,
    citation_count=0, is_open_access=False, methods=(), theories=(),
):
    """generate_literature_matrix() reads ORM attributes/relationships
    (paper.methods, paper.theories, paper.authors, ...), not dict keys — use
    a lightweight stand-in with the same attribute shape instead of a real
    DB-backed ResearchPaper."""
    return SimpleNamespace(
        title=title,
        authors=[SimpleNamespace(full_name=a) for a in authors],
        published_year=published_year,
        journal=journal,
        doi=doi,
        citation_count=citation_count,
        is_open_access=is_open_access,
        methods=[SimpleNamespace(method_name=m) for m in methods],
        theories=[SimpleNamespace(theory_name=t) for t in theories],
    )


class TestGenerateLiteratureMatrix:
    def test_returns_list_given_papers(self):
        papers = [_make_paper(title="Test Paper", authors=["Smith J"], citation_count=5, is_open_access=True)]
        result = generate_literature_matrix(papers)
        assert isinstance(result, list)
        assert len(result) == 1

    def test_matrix_row_has_required_keys(self):
        papers = [_make_paper(title="Paper A", published_year=2019)]
        row = generate_literature_matrix(papers)[0]
        for key in ("title", "authors", "year", "journal", "doi", "theories_used", "methods_used", "is_open_access", "citation_count"):
            assert key in row


# ---------------------------------------------------------------------------
# AI service — generate_conceptual_framework
# ---------------------------------------------------------------------------
class TestGenerateConceptualFramework:
    def test_returns_dict_with_required_keys(self):
        fw = generate_conceptual_framework("economic growth", ["GDP"], ["investment", "trade"])
        for key in ("title", "theoretical_foundation", "independent_variables", "dependent_variable", "moderating_factors", "proposed_relationships"):
            assert key in fw

    def test_independent_variables_match_input(self):
        fw = generate_conceptual_framework("health", ["mortality"], ["income", "education"])
        assert "income" in fw["independent_variables"] or "education" in fw["independent_variables"]


# ---------------------------------------------------------------------------
# AI service — generate_hypotheses
# ---------------------------------------------------------------------------
class TestGenerateHypotheses:
    def test_returns_list_of_strings(self):
        hs = generate_hypotheses("poverty", ["economic growth"], ["GDP", "income"])
        assert isinstance(hs, list)
        assert all(isinstance(h, str) for h in hs)

    def test_returns_at_least_one_hypothesis(self):
        hs = generate_hypotheses("trade", ["comparative advantage"], ["exports"])
        assert len(hs) >= 1


# ---------------------------------------------------------------------------
# AI service — identify_research_gaps
# ---------------------------------------------------------------------------
class TestIdentifyResearchGaps:
    def test_returns_list_of_strings(self):
        # Signature is (papers, topic) — matches how the /research router calls it.
        gaps = identify_research_gaps([], "climate change")
        assert isinstance(gaps, list)
        assert all(isinstance(g, str) for g in gaps)


# ---------------------------------------------------------------------------
# Export service — BibTeX
# ---------------------------------------------------------------------------
class TestExportBibtex:
    PAPER = {
        "title": "Test Article",
        "authors": "Doe J; Smith A",
        "year": 2022,
        "journal": "African Studies",
        "doi": "10.1234/test",
        "abstract": "An abstract.",
    }

    def test_contains_article_entry(self):
        result = export_bibtex([self.PAPER])
        assert "@article{" in result

    def test_contains_title(self):
        result = export_bibtex([self.PAPER])
        assert "Test Article" in result

    def test_contains_doi(self):
        result = export_bibtex([self.PAPER])
        assert "10.1234/test" in result

    def test_empty_list_returns_empty_string(self):
        result = export_bibtex([])
        assert result == ""

    def test_multiple_papers_separated(self):
        result = export_bibtex([self.PAPER, self.PAPER])
        assert result.count("@article{") == 2


# ---------------------------------------------------------------------------
# Export service — RIS
# ---------------------------------------------------------------------------
class TestExportRis:
    PAPER = {
        "title": "Test Article",
        "authors": "Doe J; Smith A",
        "year": 2022,
        "journal": "African Studies",
        "doi": "10.1234/test",
        "abstract": "An abstract.",
    }

    def test_starts_with_type_tag(self):
        result = export_ris([self.PAPER])
        assert "TY  - JOUR" in result

    def test_ends_with_er_tag(self):
        result = export_ris([self.PAPER])
        assert "ER  -" in result

    def test_contains_title(self):
        result = export_ris([self.PAPER])
        assert "TI  - Test Article" in result

    def test_empty_list_returns_empty_string(self):
        result = export_ris([])
        assert result == ""


# ---------------------------------------------------------------------------
# Export service — CSV
# ---------------------------------------------------------------------------
class TestExportCsv:
    PAPER = {
        "title": "Test Paper",
        "authors": "Doe J",
        "year": 2021,
        "journal": "Test Journal",
        "doi": None,
        "citation_count": 3,
        "is_open_access": True,
        "topics": "poverty",
    }

    def test_returns_bytes(self):
        result = export_csv([self.PAPER])
        assert isinstance(result, bytes)

    def test_contains_header(self):
        result = export_csv([self.PAPER]).decode("utf-8")
        assert "title" in result
        assert "authors" in result

    def test_contains_data(self):
        result = export_csv([self.PAPER]).decode("utf-8")
        assert "Test Paper" in result


# ---------------------------------------------------------------------------
# Export service — Excel
# ---------------------------------------------------------------------------
class TestExportExcel:
    PAPER = {
        "title": "Test Paper",
        "authors": "Doe J",
        "year": 2021,
        "journal": "Test Journal",
        "doi": None,
        "citation_count": 3,
        "is_open_access": True,
        "topics": "poverty",
    }

    def test_returns_bytes(self):
        result = export_excel([self.PAPER])
        assert isinstance(result, bytes)

    def test_valid_xlsx_magic_bytes(self):
        result = export_excel([self.PAPER])
        # XLSX files are ZIP archives starting with PK
        assert result[:2] == b"PK"

    def test_empty_list_returns_valid_xlsx(self):
        result = export_excel([])
        assert result[:2] == b"PK"


# ---------------------------------------------------------------------------
# REST endpoint — GET /api/v1/research/sources
# ---------------------------------------------------------------------------
class TestSourcesEndpoint:
    # Applied fresh right before each test in this class rather than once at
    # module import: other test files' `client` fixtures call
    # app.dependency_overrides.clear() at teardown, which would otherwise wipe
    # a module-level override set before this class's tests get to run.
    @pytest.fixture(autouse=True)
    def _use_isolated_db(self):
        app.dependency_overrides[get_db] = _override_get_db
        yield
        app.dependency_overrides.pop(get_db, None)

    def test_returns_200(self):
        response = client.get("/api/v1/research/sources")
        assert response.status_code == 200

    def test_returns_list(self):
        response = client.get("/api/v1/research/sources")
        data = response.json()
        assert isinstance(data, list)


# ---------------------------------------------------------------------------
# REST endpoint — GET /api/v1/research/search (mocked connector)
# ---------------------------------------------------------------------------
class TestSearchEndpoint:
    def test_missing_query_returns_422(self):
        response = client.get("/api/v1/research/search")
        assert response.status_code == 422

    @patch("app.routers.research.OpenAlexConnector")
    def test_search_returns_results_shape(self, mock_cls):
        mock_connector = MagicMock()
        mock_connector.search.return_value = []
        mock_cls.return_value = mock_connector

        response = client.get("/api/v1/research/search?q=poverty&source=openalex")
        assert response.status_code == 200
        body = response.json()
        assert "query" in body
        assert "results" in body


# ---------------------------------------------------------------------------
# REST endpoint — POST /api/v1/research/theory-recommendation
# ---------------------------------------------------------------------------
class TestTheoryRecommendationEndpoint:
    def test_valid_request_returns_200(self):
        response = client.post(
            "/api/v1/research/theory-recommendation",
            json={"topic": "financial inclusion"},
        )
        assert response.status_code == 200

    def test_response_has_recommended_theories(self):
        response = client.post(
            "/api/v1/research/theory-recommendation",
            json={"topic": "poverty"},
        )
        data = response.json()
        assert "recommended_theories" in data
        assert isinstance(data["recommended_theories"], list)

    def test_missing_topic_returns_422(self):
        response = client.post("/api/v1/research/theory-recommendation", json={})
        assert response.status_code == 422


# ---------------------------------------------------------------------------
# REST endpoint — POST /api/v1/research/method-recommendation
# ---------------------------------------------------------------------------
class TestMethodRecommendationEndpoint:
    def test_valid_request_returns_200(self):
        response = client.post(
            "/api/v1/research/method-recommendation",
            json={"topic": "panel data regression"},
        )
        assert response.status_code == 200

    def test_response_has_recommended_methods(self):
        response = client.post(
            "/api/v1/research/method-recommendation",
            json={"topic": "survey data"},
        )
        data = response.json()
        assert "recommended_methods" in data


# ---------------------------------------------------------------------------
# REST endpoint — POST /api/v1/research/variable-recommendation
# ---------------------------------------------------------------------------
class TestVariableRecommendationEndpoint:
    def test_valid_request_returns_200(self):
        response = client.post(
            "/api/v1/research/variable-recommendation",
            json={"topic": "FDI determinants"},
        )
        assert response.status_code == 200

    def test_response_shape(self):
        response = client.post(
            "/api/v1/research/variable-recommendation",
            json={"topic": "economic growth"},
        )
        data = response.json()
        assert "recommended_variables" in data
        assert "african_datasets" in data
        assert "hypotheses" in data


# ---------------------------------------------------------------------------
# REST endpoint — POST /api/v1/research/export
# ---------------------------------------------------------------------------
class TestExportEndpoint:
    PAPERS = [
        {
            "title": "Test Paper",
            "authors": "Doe J",
            "year": 2022,
            "journal": "Test Journal",
            "doi": "10.1/test",
        }
    ]

    def test_bibtex_export(self):
        response = client.post(
            "/api/v1/research/export",
            json={"papers": self.PAPERS, "format": "bibtex"},
        )
        assert response.status_code == 200
        assert "@article{" in response.text

    def test_ris_export(self):
        response = client.post(
            "/api/v1/research/export",
            json={"papers": self.PAPERS, "format": "ris"},
        )
        assert response.status_code == 200
        assert "TY  - JOUR" in response.text

    def test_csv_export(self):
        response = client.post(
            "/api/v1/research/export",
            json={"papers": self.PAPERS, "format": "csv"},
        )
        assert response.status_code == 200
        assert "title" in response.text

    def test_excel_export(self):
        response = client.post(
            "/api/v1/research/export",
            json={"papers": self.PAPERS, "format": "excel"},
        )
        assert response.status_code == 200
        assert response.content[:2] == b"PK"

    def test_unknown_format_returns_400(self):
        response = client.post(
            "/api/v1/research/export",
            json={"papers": self.PAPERS, "format": "docx"},
        )
        assert response.status_code == 400
