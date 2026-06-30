from fastapi import APIRouter, Depends, HTTPException, Query, BackgroundTasks
from sqlalchemy.orm import Session
from app.database import get_db, SessionLocal
from app.models.country import Country
from app.schemas.macro_data import MacroDataResponse
from app.services import worldbank_connector

router = APIRouter(prefix="/macro-data", tags=["Macro Data"])


def _require_country(iso3: str, db: Session) -> Country:
    country = db.query(Country).filter(Country.iso3 == iso3, Country.is_active == True).first()
    if not country:
        raise HTTPException(status_code=404, detail=f"Country '{iso3}' not found")
    return country


def _sync_with_own_session(iso3: str) -> None:
    db = SessionLocal()
    try:
        worldbank_connector.sync_macro_data(db, iso3)
    finally:
        db.close()


@router.get("", response_model=MacroDataResponse)
def get_macro_data(
    country: str = Query(..., description="ISO3 country code (e.g. NGA, RWA)"),
    db: Session = Depends(get_db),
):
    iso3 = country.upper()
    _require_country(iso3, db)
    result = worldbank_connector.get_macro_data(db, iso3)
    if not result:
        raise HTTPException(status_code=404, detail=f"No data found for {iso3}")
    return result


@router.post("/sync/{iso3}", status_code=202)
def sync_country(iso3: str, background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    iso3 = iso3.upper()
    _require_country(iso3, db)
    background_tasks.add_task(_sync_with_own_session, iso3)
    return {"message": f"Sync started for {iso3}", "status": "accepted"}
