from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.country import Country
from app.schemas.country import CountryResponse

router = APIRouter(prefix="/countries", tags=["Countries"])


@router.get("", response_model=list[CountryResponse])
def list_countries(db: Session = Depends(get_db)):
    return db.query(Country).order_by(Country.name).all()
