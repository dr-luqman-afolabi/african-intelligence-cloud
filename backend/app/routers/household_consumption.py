"""Public metadata API for EPAR household consumption-by-source files."""
from fastapi import APIRouter

from app.services.household_consumption_service import get_catalog

router = APIRouter(prefix="/consumption", tags=["Household Consumption"])


@router.get("/catalog", summary="Harmonized household food-consumption source catalog")
def consumption_catalog(country_iso3: str | None = None, survey: str | None = None):
    return get_catalog(country_iso3=country_iso3, survey=survey)
