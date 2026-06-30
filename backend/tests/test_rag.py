"""Tests for the RAG (AI Research Assistant) endpoint."""
import pytest
from fastapi.testclient import TestClient


def test_rag_query_basic(client: TestClient):
    resp = client.post("/api/v1/rag/query", json={"query": "What is GDP growth in Nigeria?"})
    assert resp.status_code == 200
    body = resp.json()
    assert "answer" in body
    assert "sources" in body
    assert "query_id" in body
    assert isinstance(body["answer"], str)
    assert len(body["answer"]) > 0


def test_rag_query_with_history(client: TestClient):
    history = [
        {"role": "user", "content": "Tell me about Africa"},
        {"role": "assistant", "content": "Africa is a continent…"},
    ]
    resp = client.post(
        "/api/v1/rag/query",
        json={"query": "What about inflation?", "history": history},
    )
    assert resp.status_code == 200
    assert "answer" in resp.json()


def test_rag_query_empty_string(client: TestClient):
    resp = client.post("/api/v1/rag/query", json={"query": ""})
    # Empty query should still return a structured response (may be empty answer)
    assert resp.status_code in (200, 422)


def test_rag_query_missing_body(client: TestClient):
    resp = client.post("/api/v1/rag/query", json={})
    assert resp.status_code == 422


def test_rag_sources_structure(client: TestClient):
    resp = client.post("/api/v1/rag/query", json={"query": "unemployment rate Kenya"})
    assert resp.status_code == 200
    sources = resp.json()["sources"]
    assert isinstance(sources, list)
    for s in sources:
        assert "source_id" in s
        assert "title" in s
        assert "score" in s
