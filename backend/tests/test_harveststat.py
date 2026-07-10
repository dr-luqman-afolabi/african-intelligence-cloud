"""Tests for HarvestStat crop statistics (national aggregation, multi-series)."""
import pandas as pd

import app.services.harveststat_service as hs


def _seed():
    hs._DF = pd.DataFrame([
        {"country": "Nigeria", "country_code": "NG", "admin_1": "Kano", "product": "Maize",
         "season_name": "Main", "harvest_year": 2015, "area": 100.0, "production": 300.0, "yield": 3.0},
        {"country": "Nigeria", "country_code": "NG", "admin_1": "Kaduna", "product": "Maize",
         "season_name": "Main", "harvest_year": 2015, "area": 100.0, "production": 100.0, "yield": 1.0},
        {"country": "Nigeria", "country_code": "NG", "admin_1": "Kano", "product": "Maize",
         "season_name": "Main", "harvest_year": 2016, "area": 200.0, "production": 800.0, "yield": 4.0},
        {"country": "Kenya", "country_code": "KE", "admin_1": "Rift", "product": "Maize",
         "season_name": "Main", "harvest_year": 2015, "area": 50.0, "production": 150.0, "yield": 3.0},
    ])
    hs._LOAD_FAILED = False


def teardown_function():
    hs._DF = None


def test_meta_structure():
    _seed()
    m = hs.get_meta()
    assert m["loaded"] is True
    assert set(m["countries"]) == {"Nigeria", "Kenya"}
    assert "Maize" in m["crops"]
    assert m["year_min"] == 2015 and m["year_max"] == 2016
    assert "yield" in m["metrics"]


def test_series_national_yield_aggregation():
    _seed()
    res = hs.get_series(["Nigeria"], ["Maize"], metric="yield")
    assert len(res["series"]) == 1
    pts = {p["x"]: p["value"] for p in res["series"][0]["points"]}
    assert pts["2015"] == 2.0   # (300+100)/(100+100)
    assert pts["2016"] == 4.0


def test_series_is_multi_series():
    _seed()
    res = hs.get_series(["Nigeria", "Kenya"], ["Maize"], metric="production")
    assert len(res["series"]) == 2  # one line per country
    nga = [s for s in res["series"] if s["country"] == "Nigeria"][0]
    assert {p["x"]: p["value"] for p in nga["points"]}["2015"] == 400.0


def test_series_filters_by_admin1():
    _seed()
    res = hs.get_series(["Nigeria"], ["Maize"], metric="yield", admin_1="Kano")
    pts = {p["x"]: p["value"] for p in res["series"][0]["points"]}
    assert pts["2015"] == 3.0  # only Kano: 300/100
