"""Tests for the EPAR indicator estimates service (multi-series time series)."""
import pandas as pd

import app.services.epar_indicators_service as epar


def _seed():
    df = pd.DataFrame([
        # Nigeria fertilizer adoption, two waves
        {"Geography": "Nigeria", "Instrument": "Nigeria GHS Wave 1", "Year": "2010-11",
         "indicatorcategory": "Adoption", "indicatorname": "Fertilizer use", "units": "Proportion",
         "commoditydisaggregation": "N/A", "genderdisaggregation": "All plot managers",
         "hhfarmsizedisaggregation": "N/A", "ruraltotalpopulation": "Rural households",
         "mean": 0.59, "sd": 0.4, "p50": 1.0, "N": 3380},
        {"Geography": "Nigeria", "Instrument": "Nigeria GHS Wave 2", "Year": "2012-13",
         "indicatorcategory": "Adoption", "indicatorname": "Fertilizer use", "units": "Proportion",
         "commoditydisaggregation": "N/A", "genderdisaggregation": "All plot managers",
         "hhfarmsizedisaggregation": "N/A", "ruraltotalpopulation": "Rural households",
         "mean": 0.62, "sd": 0.4, "p50": 1.0, "N": 3200},
        # Ethiopia fertilizer adoption, one wave
        {"Geography": "Ethiopia", "Instrument": "Ethiopia ESS Wave 1", "Year": "2011-12",
         "indicatorcategory": "Adoption", "indicatorname": "Fertilizer use", "units": "Proportion",
         "commoditydisaggregation": "N/A", "genderdisaggregation": "All plot managers",
         "hhfarmsizedisaggregation": "N/A", "ruraltotalpopulation": "Rural households",
         "mean": 0.53, "sd": 0.5, "p50": 1.0, "N": 4000},
    ])
    df["_wave"] = df["Instrument"].map(epar._wave_num)
    df["_year"] = df["Year"].map(epar._year_start)
    epar._DF = df
    epar._LOAD_FAILED = False


def teardown_function():
    epar._DF = None


def test_meta_structure():
    _seed()
    m = epar.get_meta()
    assert m["loaded"] is True
    assert set(m["countries"]) == {"Nigeria", "Ethiopia"}
    assert "Adoption" in m["categories"]
    assert "Fertilizer use" in m["indicators_by_category"]["Adoption"]


def test_series_is_multi_series_one_per_country():
    _seed()
    res = epar.get_series(["Nigeria", "Ethiopia"], ["Fertilizer use"])
    assert len(res["series"]) == 2  # 3 lines-in-one-graph capability: one series per country
    nga = [s for s in res["series"] if s["country"] == "Nigeria"][0]
    assert [p["value"] for p in nga["points"]] == [0.59, 0.62]
    assert nga["units"] == "Proportion"


def test_series_filters_by_gender():
    _seed()
    res = epar.get_series(["Nigeria"], ["Fertilizer use"], gender="Female plot managers")
    assert res["series"] == []  # none match that disaggregation


def test_wave_and_year_parsing():
    assert epar._wave_num("Nigeria GHS Wave 3") == 3
    assert epar._year_start("2015-16") == 2015
