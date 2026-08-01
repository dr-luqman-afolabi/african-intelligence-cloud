"""Spatial analysis API router (SCAFFOLD).

Not registered in main.py yet - see MICRODATA_GIS_FEATURE_PLAN.md before
enabling. These are stub endpoints only; no real GIS/microdata processing
is wired up yet.
"""
from __future__ import annotations

from fastapi import APIRouter, HTTPException

router = APIRouter(prefix="/spatial", tags=["Spatial Analysis (scaffold)"])


@router.get("/poverty-map/{country_iso3}")
def get_poverty_map(country_iso3: str):
  raise HTTPException(status_code=501, detail="Scaffold stub: spatial poverty mapping not yet implemented.")

@router.get("/boundaries/{country_iso3}")
def get_admin_boundaries(country_iso3: str):
  raise HTTPException(status_code=501, detail="Scaffold stub: admin boundary source not yet wired up.")
  
