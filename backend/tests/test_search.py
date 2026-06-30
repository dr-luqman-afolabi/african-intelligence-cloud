"""Tests for the semantic search endpoint."""
import pytest
from fastapi.testclient import TestClient


def test_semantic_search_returns_results(client: TestClient):
    resp = client.get("/api/v1/search/semantic", params={"q": "GDP growth"})
    assert resp.status_code == 200
    results = resp.json()
    assert isinstance(results, list)


def test_semantic_search_result_structure(client: TestClient):
    resp = client.get("/api/v1/search/semantic", params={"q": "inflation"})
    assert resp.status_code == 200
    for r in resp.json():
        assert "dataset_id" in r
        assert "title" in r
        assert "score" in r
        assert isinstance(r["score"], float)


def test_semantic_search_limit_respected(client: TestClient):
    resp = client.get("/api/v1/search/semantic", params={"q": "poverty", "limit": 3})
    assert resp.status_code == 200
    assert len(resp.json()) <= 3


def test_semantic_search_limit_min(client: TestClient):
    resp = client.get("/api/v1/search/semantic", params={"q": "trade", "limit": 0})
    assert resp.status_code == 422


def test_semantic_search_limit_max(client: TestClient):
    resp = client.get("/api/v1/search/semantic", params={"q": "health", "limit": 51})
    assert resp.status_code == 422


def test_semantic_search_missing_query(client: TestClient):
    resp = client.get("/api/v1/search/semantic")
    assert resp.status_code == 422


def test_semantic_search_no_results(client: TestClient):
    resp = client.get("/api/v1/search/semantic", params={"q": "xyzabcnonexistentterm123"})
    assert resp.status_code == 200
    assert resp.json() == []
