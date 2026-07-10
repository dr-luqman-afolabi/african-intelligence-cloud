"""Tests for AIC Intelligence: NL planning, heuristic routing, and auto-cleaning."""
import io

import pandas as pd


def _auth_headers(client, email="intel_user@aic.africa"):
    client.post("/api/v1/auth/register",
                json={"email": email, "full_name": "Intel User", "password": "pass1234"})
    resp = client.post("/api/v1/auth/login", json={"email": email, "password": "pass1234"})
    return {"Authorization": f"Bearer {resp.json()['access_token']}"}


def _upload_csv(client, headers):
    content = (
        b"pcexp,district,hhweight\n"
        b"50,Kigali,1\n800,Kigali,1\n1200,Huye,1\n300,Huye,1\n,Huye,1\n"
    )
    resp = client.post(
        "/api/v1/microdata/upload",
        data={"name": "Intel HH", "country_iso3": "RWA"},
        files=[("file", ("hh.csv", io.BytesIO(content), "text/csv"))],
        headers=headers,
    )
    assert resp.status_code in (200, 201), resp.text
    return resp.json()["id"]


# -- unit: heuristic planner --------------------------------------------------

def test_planner_routes_poverty_and_spatial():
    from app.services.aic_intelligence_service import build_plan
    cols = [{"name": "pcexp", "label": "per capita expenditure", "dtype": "float"},
            {"name": "district", "label": "district"},
            {"name": "hhweight", "dtype": "float"}]
    p1 = build_plan("What is the poverty rate by district at a line of 2.15?", cols)
    assert p1["analysis"] == "poverty"
    assert p1["parameters"]["welfare_variable"] == "pcexp"
    assert p1["parameters"]["poverty_line"] == 2.15

    p2 = build_plan("Show poverty hotspots on a map across districts", cols)
    assert p2["analysis"] == "spatial-poverty"
    assert p2["parameters"]["geo_variable"] == "district"

    p3 = build_plan("Which areas have the highest crop yields?", cols)
    assert p3["analysis"] == "agriculture"


# -- API: plan ----------------------------------------------------------------

def test_plan_endpoint_requires_auth(client):
    resp = client.post("/api/v1/intelligence/plan",
                       json={"dataset_id": "00000000-0000-0000-0000-000000000001", "question": "poverty?"})
    assert resp.status_code in (401, 403)


def test_plan_endpoint_returns_plan(client):
    headers = _auth_headers(client)
    ds_id = _upload_csv(client, headers)
    resp = client.post("/api/v1/intelligence/plan",
                       json={"dataset_id": ds_id, "question": "poverty rate by district, line 300"},
                       headers=headers)
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["analysis"] == "poverty"
    assert body["parameters"]["poverty_line"] == 300
    assert body["engine"] in ("heuristic", "gemini")
    assert isinstance(body["cleaning_steps"], list) and body["cleaning_steps"]


# -- API: clean ---------------------------------------------------------------

def test_clean_endpoint_creates_cleaned_dataset(client):
    headers = _auth_headers(client)
    ds_id = _upload_csv(client, headers)
    # Plan first to get cleaning steps, then clean.
    plan = client.post("/api/v1/intelligence/plan",
                       json={"dataset_id": ds_id, "question": "poverty by district, drop rows missing pcexp"},
                       headers=headers).json()
    resp = client.post("/api/v1/intelligence/clean",
                       json={"dataset_id": ds_id, "cleaning_steps": plan["cleaning_steps"]},
                       headers=headers)
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["cleaned_dataset_id"] and body["cleaned_dataset_id"] != ds_id
    assert body["row_count"] <= 5
    assert any("Rows:" in line for line in body["report"])

    # The cleaned dataset is a real dataset in the shared catalog.
    listing = client.get("/api/v1/microdata/datasets", headers=headers).json()
    assert any(it["id"] == body["cleaned_dataset_id"] for it in listing["items"])
