from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.services.survey_service import list_surveys, get_survey, list_rounds

router = APIRouter(prefix="/surveys", tags=["Survey Registry"])


@router.get("", summary="List survey programmes")
def list_survey_programmes(
    series: str | None = None,
    country_iso3: str | None = None,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
):
    surveys = list_surveys(db, series=series, country_iso3=country_iso3, skip=skip, limit=limit)
    return [_survey_dict(s) for s in surveys]


@router.get("/{survey_id}", summary="Get survey programme details")
def get_survey_detail(survey_id: str, db: Session = Depends(get_db)):
    survey = get_survey(db, survey_id)
    if survey is None:
        raise HTTPException(status_code=404, detail=f"Survey '{survey_id}' not found")
    return _survey_dict(survey)


@router.get("/{survey_id}/rounds", summary="List survey rounds")
def get_survey_rounds(survey_id: str, db: Session = Depends(get_db)):
    survey = get_survey(db, survey_id)
    if survey is None:
        raise HTTPException(status_code=404, detail=f"Survey '{survey_id}' not found")
    rounds = list_rounds(db, survey_id)
    return [_round_dict(r) for r in rounds]


def _survey_dict(s) -> dict:
    return {
        "survey_id": s.survey_id,
        "title": s.title,
        "series": s.series,
        "source_id": s.source_id,
        "country_iso3": s.country_iso3,
        "primary_topic": s.primary_topic,
        "requires_approval": s.requires_approval,
        "redistribution_allowed": s.redistribution_allowed,
        "microdata_available": s.microdata_available,
        "access_url": s.access_url,
        "documentation_url": s.documentation_url,
        "tags": s.tags or [],
    }


def _round_dict(r) -> dict:
    return {
        "id": str(r.id),
        "survey_id": r.survey_id,
        "round_label": r.round_label,
        "year_start": r.year_start,
        "year_end": r.year_end,
        "sample_size": r.sample_size,
        "fieldwork_start": r.fieldwork_start,
        "fieldwork_end": r.fieldwork_end,
        "catalog_id": r.catalog_id,
        "data_available": r.data_available,
    }
