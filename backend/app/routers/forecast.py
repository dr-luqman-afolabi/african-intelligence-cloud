"""Public crop-forecasting endpoint."""
from __future__ import annotations

from fastapi import APIRouter, Query

from app.services import forecast_service

router = APIRouter(prefix="/forecast", tags=["Forecasting"])


@router.get("/models")
def list_models() -> dict:
    return {
        "models": [
            {"id": "ensemble", "label": "Ensemble (recommended)"},
            {"id": "arima", "label": "ARIMA (1,1,1)"},
            {"id": "ets", "label": "Holt exponential smoothing"},
            {"id": "linear", "label": "Linear trend"},
        ],
        "metrics": {"yield": "Yield (t/ha)", "production": "Production (t)", "area": "Area (ha)"},
        "min_history": forecast_service._MIN_POINTS,
        "max_horizon": 15,
    }


@router.get("/crop")
def forecast_crop(
    country: str = Query(...),
    crop: str = Query(...),
    metric: str = Query("yield"),
    horizon: int = Query(5, ge=1, le=15),
    admin_1: str | None = Query(None),
    season: str | None = Query(None),
) -> dict:
    return forecast_service.forecast(
        country=country, crop=crop, metric=metric,
        horizon=horizon, admin_1=admin_1, season=season,
    )
