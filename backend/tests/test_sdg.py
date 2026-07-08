"""Tests for the SDG analytics endpoints."""
import pytest
from fastapi.testclient import TestClient


def test_sdg_goals_returns_17(client: TestClient):
    resp = client.get("/api/v1/sdg/goals")
    assert resp.status_code == 200
    goals = resp.json()
    assert len(goals) == 17


def test_sdg_goals_structure(client: TestClient):
    resp = client.get("/api/v1/sdg/goals")
    assert resp.status_code == 200
    for goal in resp.json():
        assert "goal_number" in goal
        assert "title" in goal
        assert "description" in goal
        assert "indicators" in goal
        assert 1 <= goal["goal_number"] <= 17


def test_sdg_goals_numbers_are_unique(client: TestClient):
    resp = client.get("/api/v1/sdg/goals")
    numbers = [g["goal_number"] for g in resp.json()]
    assert sorted(numbers) == list(range(1, 18))


def test_sdg_data_valid_goal(client: TestClient):
    resp = client.get("/api/v1/sdg/data", params={"goal": 1})
    assert resp.status_code == 200
    body = resp.json()
    assert "goal_number" in body
    assert "series" in body
    assert isinstance(body["series"], list)


def test_sdg_data_with_country_filter(client: TestClient):
    resp = client.get("/api/v1/sdg/data", params={"goal": 1, "country": "NGA"})
    assert resp.status_code == 200


def test_sdg_series_include_country_breakdown(client: TestClient):
    """Every series must carry a per-country latest-value breakdown with
    country names and regions, so the UI can show who is where — not just a
    faceless Africa average."""
    resp = client.get("/api/v1/sdg/data", params={"goal": 3})
    assert resp.status_code == 200
    for s in resp.json()["series"]:
        assert "country_breakdown" in s
        for entry in s["country_breakdown"]:
            assert "country_iso3" in entry
            assert "country_name" in entry
            assert "region" in entry
            assert "year" in entry
            assert "value" in entry


def test_sdg_data_goal_out_of_range_low(client: TestClient):
    resp = client.get("/api/v1/sdg/data", params={"goal": 0})
    assert resp.status_code == 422


def test_sdg_data_goal_out_of_range_high(client: TestClient):
    resp = client.get("/api/v1/sdg/data", params={"goal": 18})
    assert resp.status_code == 422


def test_sdg_data_missing_goal(client: TestClient):
    resp = client.get("/api/v1/sdg/data")
    assert resp.status_code == 422


@pytest.mark.parametrize("goal", range(1, 18))
def test_all_sdg_goals_data_accessible(client: TestClient, goal: int):
    resp = client.get("/api/v1/sdg/data", params={"goal": goal})
    assert resp.status_code == 200
