"""SDG analytics router — /api/v1/sdg"""

from __future__ import annotations

from typing import List, Optional

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.database import get_db
from app.services import sdg_service

router = APIRouter(prefix="/sdg", tags=["SDG"])


class SDGIndicatorMapping(BaseModel):
    sdg_target: str
    indicator_code: str
    indicator_name: str
    available_countries: int
    latest_year: Optional[int]


class SDGGoal(BaseModel):
    goal_number: int
    title: str
    description: str
    indicators: List[SDGIndicatorMapping]


@router.get("/goals", response_model=List[SDGGoal])
def list_sdg_goals(db: Session = Depends(get_db)):
    return sdg_service.get_goals(db)


@router.get("/data")
def get_sdg_data(
    goal: int = Query(..., ge=1, le=17),
    country: Optional[str] = Query(None),
    db: Session = Depends(get_db),
):
    return sdg_service.get_sdg_data(goal, country, db)
