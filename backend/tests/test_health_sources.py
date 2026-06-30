"""Tests for the /health/sources endpoint."""
import pytest
from fastapi.testclient import TestClient


def test_health_sources_returns_ok(client: TestClient):
    resp = client.get("/api/v1/health/sources")
    assert resp.status_code == 200


def test_health_sources_structure(client: TestClient):
    resp = client.get("/api/v1/health/sources")
    body = resp.json()
    assert "total_sources" in body
    assert "sources" in body
    assert "summary" in body
    assert "healthy" in body["summary"]
    assert "unhealthy" in body["summary"]


def test_health_sources_list_non_empty(client: TestClient):
    resp = client.get("/api/v1/health/sources")
    body = resp.json()
    assert body["total_sources"] > 0
    assert len(body["sources"]) > 0


def test_health_sources_pagination(client: TestClient):
    resp = client.get("/api/v1/health/sources", params={"limit": 2, "skip": 0})
    assert resp.status_code == 200
    assert len(resp.json()["sources"]) <= 2


def test_health_sources_healthy_only_filter(client: TestClient):
    resp = client.get("/api/v1/health/sources", params={"healthy_only": True})
    assert resp.status_code == 200
    for source in resp.json()["sources"]:
        assert source["healthy"] is True


def test_single_source_health(client: TestClient):
    sources_resp = client.get("/api/v1/health/sources")
    sources = sources_resp.json()["sources"]
    if not sources:
        pytest.skip("No sources available")
    source_id = sources[0]["source_id"]
    resp = client.get(f"/api/v1/health/sources/{source_id}")
    assert resp.status_code == 200
    body = resp.json()
    assert body["source_id"] == source_id


def test_single_source_health_unknown(client: TestClient):
    resp = client.get("/api/v1/health/sources/unknown_source_xyz")
    assert resp.status_code == 404
