from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.indicator import Indicator
from app.schemas.indicator import IndicatorResponse

router = APIRouter(prefix="/indicators", tags=["Indicators"])


@router.get("", response_model=list[IndicatorResponse])
def list_indicators(db: Session = Depends(get_db)):
    return db.query(Indicator).order_by(Indicator.category, Indicator.name).all()
