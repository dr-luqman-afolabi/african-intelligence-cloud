"""Tests for the /health/sources endpoint."""
import time
from datetime import datetime, timezone
from types import SimpleNamespace

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


def test_single_source_health_timeout(client: TestClient, monkeypatch):
    import app.routers.health_sources as health_router

    class SlowConnector:
        @staticmethod
        def health_check():
            time.sleep(0.05)

    monkeypatch.setattr(health_router, "get_connector", lambda _source_id: SlowConnector())
    monkeypatch.setattr(health_router, "_AGGREGATE_DEADLINE_SECONDS", 0.001)

    resp = client.get("/api/v1/health/sources/slow_source")
    assert resp.status_code == 200
    body = resp.json()
    assert body["source_id"] == "slow_source"
    assert body["healthy"] is False
    assert body["message"] == "health check timed out"

def test_health_sources_survives_unavailable_watermarks(client: TestClient, monkeypatch):
    import app.routers.health_sources as health_router

    class HealthyConnector:
        def __init__(self, source_id: str):
            self.source_id = source_id

        def health_check(self):
            return SimpleNamespace(
                source_id=self.source_id,
                healthy=True,
                latency_ms=1.0,
                message="ok",
                checked_at=datetime.now(timezone.utc),
            )

    monkeypatch.setattr(
        health_router,
        "list_watermarks",
        lambda _db: (_ for _ in ()).throw(RuntimeError("watermark table unavailable")),
    )
    monkeypatch.setattr(
        health_router,
        "get_connector",
        lambda source_id: HealthyConnector(source_id),
    )

    resp = client.get("/api/v1/health/sources", params={"limit": 1})
    assert resp.status_code == 200
    body = resp.json()
    assert len(body["sources"]) == 1
    assert body["sources"][0]["healthy"] is True
    assert body["sources"][0]["last_synced_at"] is None



def test_health_sources_snapshot_does_not_probe_connectors(client: TestClient, monkeypatch):
    import app.routers.health_sources as health_router

    def unexpected_probe(_source_id):
        raise AssertionError("snapshot mode must not construct or probe connectors")

    monkeypatch.setattr(health_router, "get_connector", unexpected_probe)

    resp = client.get(
        "/api/v1/health/sources",
        params={"limit": 3, "probe": False},
    )

    assert resp.status_code == 200
    body = resp.json()
    assert len(body["sources"]) == 3
    assert body["summary"]["unknown"] == 3
    assert all(source["healthy"] is None for source in body["sources"])
    assert all(source["message"] == "Registered; live probe pending" for source in body["sources"])
