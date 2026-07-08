"""Tests for the LSMS & Microdata Analytics Engine: variable mapping
auto-detection, agriculture productivity, and diversification indices."""
import io
import zipfile

import pandas as pd
import pytest

from app.services.agriculture_analysis_service import (
    compute_agriculture_stats,
    compute_grouped_agriculture,
)
from app.services.diversification_analysis_service import (
    compute_diversification_stats,
    herfindahl_index,
    shannon_index,
    simpson_index,
)
from app.services.microdata_metadata_service import extract_supported_file_from_zip
from app.services.variable_mapping_service import suggest_mappings


# -- Variable mapping auto-detection ------------------------------------------


def test_suggest_mappings_detects_common_lsms_columns():
    variables = [
        {"variable_name": "hhid", "variable_label": "Household identifier"},
        {"variable_name": "welfare_pc", "variable_label": "Per capita welfare aggregate"},
        {"variable_name": "hhweight", "variable_label": "Household sampling weight"},
        {"variable_name": "district", "variable_label": "District of residence"},
        {"variable_name": "sex_hh_head", "variable_label": "Sex of household head"},
        {"variable_name": "random_col_123", "variable_label": None},
    ]
    suggestions = suggest_mappings(variables)
    by_concept = {s["standard_concept"]: s["raw_variable_name"] for s in suggestions}

    assert by_concept["household_id"] == "hhid"
    assert by_concept["welfare"] == "welfare_pc"
    assert by_concept["weight"] == "hhweight"
    assert by_concept["district"] == "district"
    assert "random_col_123" not in by_concept.values()


def test_suggest_mappings_returns_empty_for_no_matches():
    variables = [{"variable_name": "xyz1", "variable_label": None}, {"variable_name": "xyz2", "variable_label": None}]
    assert suggest_mappings(variables) == []


def test_suggest_mappings_each_variable_used_at_most_once():
    variables = [{"variable_name": "gender", "variable_label": None}]
    suggestions = suggest_mappings(variables)
    raw_names = [s["raw_variable_name"] for s in suggestions]
    assert len(raw_names) == len(set(raw_names))


# -- ZIP upload extraction -----------------------------------------------------


def _make_zip(files: dict[str, bytes]) -> bytes:
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as zf:
        for name, content in files.items():
            zf.writestr(name, content)
    return buf.getvalue()


def test_extract_supported_file_from_zip_picks_largest_data_file():
    zip_bytes = _make_zip({
        "readme.txt": b"not a data file",
        "codebook.csv": b"a,b\n1,2\n",
        "household.csv": b"a,b,c\n1,2,3\n4,5,6\n7,8,9\n",
    })
    content, ext, filename = extract_supported_file_from_zip(zip_bytes)
    assert ext == "csv"
    assert filename == "household.csv"
    assert content == b"a,b,c\n1,2,3\n4,5,6\n7,8,9\n"


def test_extract_supported_file_from_zip_raises_when_no_data_file():
    zip_bytes = _make_zip({"readme.txt": b"nothing useful here"})
    with pytest.raises(ValueError):
        extract_supported_file_from_zip(zip_bytes)


def test_extract_supported_file_from_zip_raises_for_invalid_zip():
    with pytest.raises(ValueError):
        extract_supported_file_from_zip(b"not a zip file at all")


# -- Agriculture analytics -----------------------------------------------------


def _agriculture_df():
    return pd.DataFrame({
        "land_ha": [1.0, 2.0, 0.5, 4.0],
        "harvest_kg": [500.0, 1600.0, 100.0, 4000.0],
        "sales_value": [1000.0, 3200.0, 0.0, 8000.0],
        "fertilizer_use": [1, 0, 0, 1],
        "district": ["A", "A", "B", "B"],
    })


_MAPPING = {"land_area": "land_ha", "crop_output": "harvest_kg", "crop_value": "sales_value", "fertilizer": "fertilizer_use"}


def test_compute_agriculture_stats_returns_expected_keys():
    stats = compute_agriculture_stats(_agriculture_df(), _MAPPING)
    for key in ("crop_yield", "value_of_production", "land_productivity", "fertilizer_adoption_rate", "market_participation_rate"):
        assert key in stats
    assert stats["n_obs"] == 4


def test_compute_agriculture_stats_crop_yield_is_output_over_land():
    df = pd.DataFrame({"land_ha": [2.0], "harvest_kg": [1000.0]})
    stats = compute_agriculture_stats(df, {"land_area": "land_ha", "crop_output": "harvest_kg"})
    assert stats["crop_yield"] == pytest.approx(500.0)


def test_compute_agriculture_stats_fertilizer_adoption_rate():
    stats = compute_agriculture_stats(_agriculture_df(), _MAPPING)
    assert stats["fertilizer_adoption_rate"] == pytest.approx(0.5)


def test_compute_agriculture_stats_omits_missing_concepts():
    df = pd.DataFrame({"land_ha": [1.0, 2.0]})
    stats = compute_agriculture_stats(df, {"land_area": "land_ha"})
    assert "crop_yield" not in stats
    assert "fertilizer_adoption_rate" not in stats


def test_compute_grouped_agriculture_groups_correctly():
    rows = compute_grouped_agriculture(_agriculture_df(), _MAPPING, "district")
    groups = {r["group"] for r in rows}
    assert groups == {"A", "B"}


# -- Diversification analytics -------------------------------------------------


def test_simpson_index_single_source_is_zero():
    shares = pd.Series([1.0, 0.0, 0.0])
    assert simpson_index(shares) == pytest.approx(0.0)


def test_simpson_index_even_sources_approaches_one():
    shares = pd.Series([0.25, 0.25, 0.25, 0.25])
    assert simpson_index(shares) == pytest.approx(0.75)


def test_shannon_index_single_source_is_zero():
    shares = pd.Series([1.0, 0.0])
    assert shannon_index(shares) == pytest.approx(0.0)


def test_herfindahl_index_is_inverse_of_diversity():
    concentrated = pd.Series([1.0, 0.0, 0.0])
    even = pd.Series([0.25, 0.25, 0.25, 0.25])
    assert herfindahl_index(concentrated) > herfindahl_index(even)


def test_compute_diversification_stats_crop_count_and_indices():
    df = pd.DataFrame({
        "maize_value": [1000.0, 0.0],
        "beans_value": [0.0, 500.0],
        "cassava_value": [500.0, 500.0],
    })
    stats = compute_diversification_stats(df, crop_columns=["maize_value", "beans_value", "cassava_value"])
    assert "crop_count" in stats
    assert "crop_simpson_index" in stats
    assert 0.0 <= stats["crop_simpson_index"] <= 1.0


def test_compute_diversification_stats_requires_at_least_two_columns():
    df = pd.DataFrame({"maize_value": [1000.0, 500.0]})
    stats = compute_diversification_stats(df, crop_columns=["maize_value"])
    assert "crop_simpson_index" not in stats


def test_compute_diversification_stats_empty_when_no_columns_supplied():
    df = pd.DataFrame({"a": [1, 2]})
    stats = compute_diversification_stats(df)
    assert stats == {"n_obs": 2}


# -- Spatial output (choropleth-ready GeoJSON merge) ----------------------------


def _square(x0: float, y0: float) -> dict:
    return {
        "type": "Polygon",
        "coordinates": [[[x0, y0], [x0 + 1, y0], [x0 + 1, y0 + 1], [x0, y0 + 1], [x0, y0]]],
    }


def test_merge_stats_with_geojson_produces_ranked_choropleth():
    from app.services.spatial_analysis_service import merge_stats_with_geojson

    geojson = {
        "type": "FeatureCollection",
        "features": [
            {"type": "Feature", "geometry": _square(0, 0), "properties": {"admin_name": "Kigali"}},
            {"type": "Feature", "geometry": _square(1, 0), "properties": {"admin_name": "Huye"}},
            {"type": "Feature", "geometry": _square(2, 0), "properties": {"admin_name": "Unmatched"}},
        ],
    }
    stats = [
        {"geo_value": "Kigali", "crop_yield": 100.0, "n_obs": 10},
        {"geo_value": "Huye", "crop_yield": 300.0, "n_obs": 8},
    ]
    merged = merge_stats_with_geojson(geojson, stats, "district", rank_field="crop_yield")

    assert merged["type"] == "FeatureCollection"
    assert len(merged["features"]) == 2  # unmatched feature dropped
    top = merged["features"][0]["properties"]
    assert top["geo_value"] == "Huye"
    assert top["rank"] == 1
    assert top["crop_yield"] == pytest.approx(300.0)


# -- ZIP upload through the API -------------------------------------------------


def test_upload_zip_dataset_via_api(client):
    # Register + login (first user in a fresh test DB is auto-verified)
    client.post(
        "/api/v1/auth/register",
        json={"email": "zip_upload@aic.africa", "full_name": "Zip User", "password": "pass1234"},
    )
    login = client.post("/api/v1/auth/login", json={"email": "zip_upload@aic.africa", "password": "pass1234"})
    headers = {"Authorization": f"Bearer {login.json()['access_token']}"}

    csv_bytes = b"consumption,weight,district\n100,1,Kigali\n900,1,Huye\n"
    zip_bytes = _make_zip({"readme.txt": b"docs", "rwanda_eicv5_2017.csv": csv_bytes})

    resp = client.post(
        "/api/v1/microdata/upload",
        data={"name": "EICV Zip Test"},
        files=[("file", ("rwanda_eicv5_2017.zip", io.BytesIO(zip_bytes), "application/zip"))],
        headers=headers,
    )
    assert resp.status_code == 201, resp.text
    body = resp.json()
    assert body["file_type"] == "csv"  # stored as the extracted inner file, not the zip
    assert body["original_filename"] == "rwanda_eicv5_2017.csv"
    assert body["row_count"] == 2
    assert body["country_iso3"] == "RWA"  # detected from the inner filename
    assert body["year"] == 2017
