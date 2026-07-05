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


@router.get("/interpret")
def interpret_macro_data(
    country: str = Query(..., description="ISO3 country code (e.g. NGA, RWA)"),
    indicators: str = Query(..., description="Comma-separated indicator codes"),
    db: Session = Depends(get_db),
):
    """Generate a data-driven narrative interpretation of one or more indicator series."""
    iso3 = country.upper()
    country_obj = _require_country(iso3, db)
    codes = [c.strip() for c in indicators.split(",") if c.strip()]
    result = worldbank_connector.get_macro_data(db, iso3)
    rows = result.get("data", [])
    sentences = []
    for code in codes:
        series = [r for r in rows if r["indicator_code"] == code]
        series.sort(key=lambda r: r["year"])
        if len(series) < 2:
            sentences.append("Not enough synced data yet for " + code + " in " + country_obj.name + ".")
            continue
        first = series[0]
        last = series[-1]
        name = first["indicator_name"]
        change = last["value"] - first["value"]
        pct = None
        if first["value"]:
            pct = change / first["value"] * 100
        direction = "increased"
        if change < 0:
            direction = "decreased"
        elif change == 0:
            direction = "remained stable"
        values = [r["value"] for r in series]
        peak = max(values)
        trough = min(values)
        peak_year = first["year"]
        trough_year = first["year"]
        for r in series:
            if r["value"] == peak:
                peak_year = r["year"]
            if r["value"] == trough:
                trough_year = r["year"]
        sentence = name + " in " + country_obj.name + " " + direction + " from " + str(round(first["value"], 2)) + " in " + str(first["year"]) + " to " + str(round(last["value"], 2)) + " in " + str(last["year"])
        if pct is not None:
            sentence = sentence + " (" + str(round(pct, 1)) + "% change)"
        sentence = sentence + ". It peaked at " + str(round(peak, 2)) + " in " + str(peak_year) + " and was lowest at " + str(round(trough, 2)) + " in " + str(trough_year) + "."
        sentences.append(sentence)
    narrative = " ".join(sentences)
    if not narrative:
        narrative = "No synced data available yet for " + country_obj.name + ". Trigger a sync for this country first."
    return {
        "country_iso3": iso3,
        "country_name": country_obj.name,
        "indicators": codes,
        "narrative": narrative,
    }
