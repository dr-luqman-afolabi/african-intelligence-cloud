"""Time-series forecasting for AIC crop indicators.

Fits several transparent, well-understood models to a single crop time series
and returns forecasts with 95% confidence intervals plus an ensemble. Models:

  * ``linear``  – ordinary-least-squares trend (numpy), CI from residual SE.
  * ``arima``   – statsmodels ARIMA, CI from the model's forecast covariance.
  * ``ets``     – Holt exponential smoothing (level+trend), CI from residual SE.
  * ``ensemble``– mean of the available model forecasts; CI is the mean band.

The history comes from ``harveststat_service.get_series`` so forecasts use the
same nationally-aggregated numbers shown on the Crop Statistics explorer. All
methods degrade gracefully: if a model can't fit (too few points, singular fit)
it is skipped rather than raising, and the ensemble uses whatever succeeded.
"""
from __future__ import annotations

import logging
import warnings
from typing import Any

import numpy as np

from app.services import harveststat_service

logger = logging.getLogger(__name__)

_Z = 1.959963984540054  # 95% normal quantile
MODELS = ("linear", "arima", "ets", "ensemble")
_MIN_POINTS = 6


def _linear(years: np.ndarray, values: np.ndarray, fyears: np.ndarray) -> dict[str, Any] | None:
    try:
        b1, b0 = np.polyfit(years, values, 1)
        fitted = b0 + b1 * years
        resid = values - fitted
        dof = max(len(values) - 2, 1)
        se = float(np.sqrt(np.sum(resid ** 2) / dof))
        pred = b0 + b1 * fyears
        band = _Z * se
        return _pack(fyears, pred, pred - band, pred + band)
    except Exception as exc:  # pragma: no cover - defensive
        logger.info("linear forecast failed: %s", exc)
        return None


def _ets(years: np.ndarray, values: np.ndarray, horizon: int, fyears: np.ndarray) -> dict[str, Any] | None:
    try:
        from statsmodels.tsa.holtwinters import ExponentialSmoothing

        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            fit = ExponentialSmoothing(values, trend="add", seasonal=None,
                                       initialization_method="estimated").fit()
        pred = np.asarray(fit.forecast(horizon), dtype=float)
        resid = np.asarray(fit.resid, dtype=float)
        se = float(np.sqrt(np.nanmean(resid ** 2))) if resid.size else 0.0
        # widen the band with the forecast horizon (uncertainty grows)
        steps = np.arange(1, horizon + 1)
        band = _Z * se * np.sqrt(steps)
        return _pack(fyears, pred, pred - band, pred + band)
    except Exception as exc:
        logger.info("ETS forecast failed: %s", exc)
        return None


def _arima(values: np.ndarray, horizon: int, fyears: np.ndarray) -> dict[str, Any] | None:
    try:
        from statsmodels.tsa.arima.model import ARIMA

        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            fit = ARIMA(values, order=(1, 1, 1)).fit()
            fc = fit.get_forecast(steps=horizon)
        pred = np.asarray(fc.predicted_mean, dtype=float)
        ci = np.asarray(fc.conf_int(alpha=0.05), dtype=float)
        return _pack(fyears, pred, ci[:, 0], ci[:, 1])
    except Exception as exc:
        logger.info("ARIMA forecast failed: %s", exc)
        return None


def _pack(fyears: np.ndarray, pred, lo, hi) -> dict[str, Any]:
    pred = np.asarray(pred, dtype=float)
    lo = np.asarray(lo, dtype=float)
    hi = np.asarray(hi, dtype=float)
    points = []
    for i, yr in enumerate(fyears):
        p = float(pred[i])
        points.append({
            "year": int(yr), "x": str(int(yr)),
            "value": round(p, 3),
            "lower": round(float(lo[i]), 3),
            "upper": round(float(hi[i]), 3),
        })
    return {"points": points}


def forecast(
    country: str,
    crop: str,
    metric: str = "yield",
    horizon: int = 5,
    admin_1: str | None = None,
    season: str | None = None,
) -> dict[str, Any]:
    horizon = max(1, min(int(horizon), 15))
    res = harveststat_service.get_series([country], [crop], metric=metric,
                                         admin_1=admin_1, season=season)
    if not res.get("loaded", True):
        return {"loaded": False, "history": [], "models": {}, "reason": "loading"}
    series = res.get("series") or []
    if not series:
        return {"loaded": True, "history": [], "models": {},
                "reason": "no_data", "units": res.get("units")}

    pts = series[0]["points"]
    years = np.array([p["year"] for p in pts], dtype=float)
    values = np.array([p["value"] for p in pts], dtype=float)
    units = series[0]["units"]

    if len(values) < _MIN_POINTS:
        return {"loaded": True, "history": pts, "models": {},
                "reason": "too_short", "min_points": _MIN_POINTS, "units": units,
                "country": country, "crop": crop, "metric": metric}

    last_year = int(years[-1])
    fyears = np.arange(last_year + 1, last_year + 1 + horizon, dtype=float)

    models: dict[str, Any] = {}
    lin = _linear(years, values, fyears)
    if lin:
        models["linear"] = lin
    ar = _arima(values, horizon, fyears)
    if ar:
        models["arima"] = ar
    et = _ets(years, values, horizon, fyears)
    if et:
        models["ets"] = et

    # ensemble = mean across available model bands
    if models:
        stacks_p, stacks_l, stacks_u = [], [], []
        for m in models.values():
            stacks_p.append([pt["value"] for pt in m["points"]])
            stacks_l.append([pt["lower"] for pt in m["points"]])
            stacks_u.append([pt["upper"] for pt in m["points"]])
        mp = np.mean(stacks_p, axis=0)
        ml = np.mean(stacks_l, axis=0)
        mu = np.mean(stacks_u, axis=0)
        models["ensemble"] = _pack(fyears, mp, ml, mu)

    return {
        "loaded": True,
        "country": country, "crop": crop, "metric": metric, "units": units,
        "horizon": horizon,
        "history": pts,
        "models": models,
        "available_models": list(models.keys()),
    }
