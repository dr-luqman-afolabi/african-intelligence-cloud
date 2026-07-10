import numpy as np
import pytest
import pandas as pd

from app.services import harveststat_service, forecast_service


@pytest.fixture
def synthetic_df(monkeypatch):
    rows = []
    for i, yr in enumerate(range(2000, 2021)):
        val = 1.4 + 0.03 * i
        rows.append(("Nigeria", "NGA", "Nat", "Maize", "Main", yr, 100.0, val * 100.0, val))
    df = pd.DataFrame(rows, columns=["country", "country_code", "admin_1", "product",
                                     "season_name", "harvest_year", "area", "production", "yield"])
    monkeypatch.setattr(harveststat_service, "_DF", df)
    monkeypatch.setattr(harveststat_service, "_LOAD_FAILED", False, raising=False)
    return df


def test_forecast_shape_and_ci(synthetic_df):
    fc = forecast_service.forecast("Nigeria", "Maize", "yield", horizon=5)
    assert fc["loaded"] is True
    assert len(fc["history"]) == 21
    # linear is numpy-only and must always be available; ensemble too
    assert "linear" in fc["models"]
    assert "ensemble" in fc["models"]
    for m in fc["models"].values():
        assert len(m["points"]) == 5
        for p in m["points"]:
            assert p["lower"] <= p["value"] <= p["upper"]
    # forecast years follow history
    assert fc["models"]["linear"]["points"][0]["year"] == 2021


def test_forecast_horizon_clamped(synthetic_df):
    fc = forecast_service.forecast("Nigeria", "Maize", "yield", horizon=50)
    assert fc["horizon"] == 15
    assert len(fc["models"]["linear"]["points"]) == 15


def test_forecast_too_short(synthetic_df, monkeypatch):
    df = synthetic_df[synthetic_df["harvest_year"] <= 2003]
    monkeypatch.setattr(harveststat_service, "_DF", df)
    fc = forecast_service.forecast("Nigeria", "Maize", "yield", horizon=5)
    assert fc["reason"] == "too_short"
    assert fc["models"] == {}


def test_forecast_no_data(synthetic_df):
    fc = forecast_service.forecast("Atlantis", "Maize", "yield")
    assert fc["reason"] == "no_data"


def test_arima_ets_when_statsmodels_present(synthetic_df):
    pytest.importorskip("statsmodels")
    fc = forecast_service.forecast("Nigeria", "Maize", "yield", horizon=4)
    assert "arima" in fc["models"]
    assert "ets" in fc["models"]
