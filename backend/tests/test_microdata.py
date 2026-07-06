"""Tests for the Microdata Analytics & Poverty Studio: metadata extraction,
FGT poverty indices, Gini coefficient, grouped poverty, and API response structure.
"""
import io

import pandas as pd
import pytest

from app.services.poverty_analysis_service import (
    compute_fgt_indices,
    compute_grouped_poverty,
    gini_coefficient,
    poverty_gap,
    poverty_headcount,
    squared_poverty_gap,
)
from app.services.microdata_metadata_service import extract_metadata


def _auth_headers(client, email="microdata_user@aic.africa"):
    client.post(
        "/api/v1/auth/register",
        json={"email": email, "full_name": "Microdata User", "password": "pass1234"},
    )
    resp = client.post("/api/v1/auth/login", json={"email": email, "password": "pass1234"})
    token = resp.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def _csv_bytes():
    return (
        b"consumption,weight,region\n"
        b"50,1,Kigali\n"
        b"800,1,Kigali\n"
        b"1200,1,Huye\n"
        b"300,1,Huye\n"
    )


def _csv_file(name="household.csv"):
    return ("file", (name, io.BytesIO(_csv_bytes()), "text/csv"))


# -- Poverty index unit tests -------------------------------------------------


def test_poverty_headcount_basic():
    welfare = pd.Series([50, 150, 250, 400])
    rate = poverty_headcount(welfare, poverty_line=200)
    assert rate == pytest.approx(0.5)


def test_poverty_gap_basic():
    welfare = pd.Series([50, 150, 250, 400])
    gap = poverty_gap(welfare, poverty_line=200)
    assert 0 < gap < 1


def test_squared_poverty_gap_le_poverty_gap():
    welfare = pd.Series([50, 150, 250, 400])
    gap = poverty_gap(welfare, poverty_line=200)
    sq_gap = squared_poverty_gap(welfare, poverty_line=200)
    assert 0 < sq_gap <= gap


def test_gini_coefficient_perfect_equality():
    welfare = pd.Series([100, 100, 100, 100])
    assert gini_coefficient(welfare) == pytest.approx(0.0, abs=1e-6)


def test_gini_coefficient_reflects_inequality():
    equal = pd.Series([100, 100, 100, 100])
    unequal = pd.Series([10, 20, 30, 1000])
    assert gini_coefficient(unequal) > gini_coefficient(equal)


def test_compute_fgt_indices_returns_expected_keys():
    df = pd.DataFrame({"consumption": [50, 150, 250, 400]})
    result = compute_fgt_indices(df, "consumption", poverty_line=200)
    for key in [
        "headcount",
        "poverty_gap",
        "squared_poverty_gap",
        "gini",
        "mean_consumption",
        "median_consumption",
        "n_obs",
    ]:
        assert key in result
    assert result["n_obs"] == 4
    assert result["headcount"] == pytest.approx(0.5)


def test_compute_grouped_poverty_groups_correctly():
    df = pd.DataFrame(
        {
            "consumption": [50, 150, 900, 1000],
            "region": ["Kigali", "Kigali", "Huye", "Huye"],
        }
    )
    rows = compute_grouped_poverty(df, "consumption", poverty_line=200, group_by="region")
    groups = {row["group"] for row in rows}
    assert groups == {"Kigali", "Huye"}
    kigali_row = next(row for row in rows if row["group"] == "Kigali")
    huye_row = next(row for row in rows if row["group"] == "Huye")
    assert kigali_row["headcount"] == pytest.approx(1.0)
    assert huye_row["headcount"] == pytest.approx(0.0)


# -- Metadata extraction -------------------------------------------------------


def test_extract_metadata_from_csv():
    metadata = extract_metadata(_csv_bytes(), "csv", "household_eicv5.csv")
    assert metadata["row_count"] == 4
    assert metadata["column_count"] == 3
    variable_names = {v["variable_name"] for v in metadata["variables"]}
    assert variable_names == {"consumption", "weight", "region"}


# -- API integration tests ----------------------------------------------------


def test_upload_requires_auth(client):
    resp = client.post(
        "/api/v1/microdata/upload", data={"name": "Test dataset"}, files=[_csv_file()]
    )
    assert resp.status_code in (401, 403)


def test_upload_and_list_dataset(client):
    headers = _auth_headers(client, email="microdata_list@aic.africa")
    resp = client.post(
        "/api/v1/microdata/upload",
        data={"name": "EICV Test Household", "country_iso3": "RWA"},
        files=[_csv_file()],
        headers=headers,
    )
    assert resp.status_code in (200, 201)
    body = resp.json()
    assert body["name"] == "EICV Test Household"
    assert body["row_count"] == 4

    list_resp = client.get("/api/v1/microdata/datasets", headers=headers)
    assert list_resp.status_code == 200
    items = list_resp.json()["items"]
    assert any(item["id"] == body["id"] for item in items)


def test_upload_and_fetch_variables(client):
    headers = _auth_headers(client, email="microdata_vars@aic.africa")
    resp = client.post(
        "/api/v1/microdata/upload",
        data={"name": "Variable Test Dataset"},
        files=[_csv_file()],
        headers=headers,
    )
    dataset_id = resp.json()["id"]

    vars_resp = client.get(
        f"/api/v1/microdata/datasets/{dataset_id}/variables", headers=headers
    )
    assert vars_resp.status_code == 200
    names = {v["variable_name"] for v in vars_resp.json()}
    assert names == {"consumption", "weight", "region"}


def test_run_poverty_analysis_via_api(client):
    headers = _auth_headers(client, email="microdata_poverty@aic.africa")
    upload_resp = client.post(
        "/api/v1/microdata/upload",
        data={"name": "Poverty Test Dataset"},
        files=[_csv_file()],
        headers=headers,
    )
    dataset_id = upload_resp.json()["id"]

    analyze_resp = client.post(
        "/api/v1/microdata/analyze/poverty",
        json={
            "dataset_id": dataset_id,
            "welfare_variable": "consumption",
            "poverty_line": 200,
            "weight_variable": "weight",
            "group_by": ["region"],
        },
        headers=headers,
    )
    assert analyze_resp.status_code == 200
    body = analyze_resp.json()
    assert body["status"] == "completed"
    assert body["job_type"] == "poverty"
    assert "headcount" in body["summary_stats"]
    assert "region" in body["tables"]
