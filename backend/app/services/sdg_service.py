"""SDG analytics service — maps SDG goals to indicator codes and queries macro_data."""

from __future__ import annotations

from typing import List, Optional

from sqlalchemy.orm import Session

from app.models.indicator import Indicator
from app.models.macro_data import MacroData

# Mapping SDG goal numbers to keyword patterns for indicator matching
SDG_GOALS = [
    {
        "goal_number": 1,
        "title": "No Poverty",
        "description": "End poverty in all its forms everywhere",
        "keywords": ["poverty", "income", "social protection", "gini"],
    },
    {
        "goal_number": 2,
        "title": "Zero Hunger",
        "description": "End hunger, achieve food security and improved nutrition",
        "keywords": ["food", "hunger", "nutrition", "agriculture", "malnutrition", "yield", "crop", "cereal"],
    },
    {
        "goal_number": 3,
        "title": "Good Health and Well-being",
        "description": "Ensure healthy lives and promote well-being for all",
        "keywords": ["health", "mortality", "life expectancy", "disease", "malaria", "hiv", "maternal", "infant"],
    },
    {
        "goal_number": 4,
        "title": "Quality Education",
        "description": "Ensure inclusive and equitable quality education",
        "keywords": ["education", "literacy", "enrollment", "school", "learning"],
    },
    {
        "goal_number": 5,
        "title": "Gender Equality",
        "description": "Achieve gender equality and empower all women and girls",
        "keywords": ["gender", "female", "women", "girls"],
    },
    {
        "goal_number": 6,
        "title": "Clean Water and Sanitation",
        "description": "Ensure availability and sustainable management of water and sanitation",
        "keywords": ["water", "sanitation", "hygiene", "wash"],
    },
    {
        "goal_number": 7,
        "title": "Affordable and Clean Energy",
        "description": "Ensure access to affordable, reliable, sustainable and modern energy",
        "keywords": ["energy", "electricity", "renewable", "fuel"],
    },
    {
        "goal_number": 8,
        "title": "Decent Work and Economic Growth",
        "description": "Promote sustained, inclusive and sustainable economic growth",
        "keywords": ["gdp", "employment", "unemployment", "labor", "labour", "growth", "economic"],
    },
    {
        "goal_number": 9,
        "title": "Industry, Innovation and Infrastructure",
        "description": "Build resilient infrastructure and foster innovation",
        "keywords": ["industry", "infrastructure", "innovation", "manufacturing", "internet"],
    },
    {
        "goal_number": 10,
        "title": "Reduced Inequalities",
        "description": "Reduce inequality within and among countries",
        "keywords": ["inequality", "gini", "income distribution"],
    },
    {
        "goal_number": 11,
        "title": "Sustainable Cities and Communities",
        "description": "Make cities and human settlements inclusive, safe, resilient and sustainable",
        "keywords": ["urban", "cities", "housing", "slum", "population"],
    },
    {
        "goal_number": 12,
        "title": "Responsible Consumption and Production",
        "description": "Ensure sustainable consumption and production patterns",
        "keywords": ["consumption", "production", "waste", "recycling"],
    },
    {
        "goal_number": 13,
        "title": "Climate Action",
        "description": "Take urgent action to combat climate change and its impacts",
        "keywords": ["climate", "emissions", "co2", "carbon", "temperature", "greenhouse", "rainfall", "precipitation"],
    },
    {
        "goal_number": 14,
        "title": "Life Below Water",
        "description": "Conserve and sustainably use the oceans, seas and marine resources",
        "keywords": ["ocean", "marine", "fisheries", "coastal"],
    },
    {
        "goal_number": 15,
        "title": "Life on Land",
        "description": "Protect, restore and promote sustainable use of terrestrial ecosystems",
        "keywords": ["forest", "land", "biodiversity", "deforestation", "ecosystem"],
    },
    {
        "goal_number": 16,
        "title": "Peace, Justice and Strong Institutions",
        "description": "Promote peaceful and inclusive societies",
        "keywords": ["governance", "corruption", "rule of law", "conflict", "violence", "democracy"],
    },
    {
        "goal_number": 17,
        "title": "Partnerships for the Goals",
        "description": "Strengthen the means of implementation",
        "keywords": ["trade", "debt", "aid", "development assistance", "remittance"],
    },
]


def _match_indicators(keywords: List[str], db: Session, limit: int = 5) -> List[dict]:
    indicators: List[Indicator] = db.query(Indicator).all()
    matched = []
    for ind in indicators:
        doc = f"{ind.name or ''} {ind.description or ''} {ind.category or ''}".lower()
        hits = sum(1 for kw in keywords if kw in doc)
        if hits > 0:
            years = (
                db.query(MacroData.year)
                .filter(MacroData.indicator_code == ind.code)
                .order_by(MacroData.year.desc())
                .first()
            )
            countries = (
                db.query(MacroData.country_iso3)
                .filter(MacroData.indicator_code == ind.code)
                .distinct()
                .count()
            )
            matched.append(
                {
                    "sdg_target": f"SDG {ind.category or 'general'}",
                    "indicator_code": ind.code,
                    "indicator_name": ind.name,
                    "available_countries": countries,
                    "latest_year": years[0] if years else None,
                    "_hits": hits,
                }
            )
    matched.sort(key=lambda x: x["_hits"], reverse=True)
    for m in matched:
        m.pop("_hits", None)
    return matched[:limit]


def get_goals(db: Session) -> List[dict]:
    result = []
    for goal in SDG_GOALS:
        indicators = _match_indicators(goal["keywords"], db)
        result.append(
            {
                "goal_number": goal["goal_number"],
                "title": goal["title"],
                "description": goal["description"],
                "indicators": indicators,
            }
        )
    return result


def get_sdg_data(goal: int, country: Optional[str], db: Session) -> dict:
    goal_meta = next((g for g in SDG_GOALS if g["goal_number"] == goal), None)
    if not goal_meta:
        return {"goal": goal, "series": []}

    indicators = _match_indicators(goal_meta["keywords"], db, limit=10)
    indicator_codes = [i["indicator_code"] for i in indicators]

    series = []
    for code in indicator_codes:
        q = db.query(MacroData).filter(MacroData.indicator_code == code)
        if country:
            q = q.filter(MacroData.country_iso3 == country.upper())
        rows = q.order_by(MacroData.year).all()
        if not rows:
            continue
        ind = db.query(Indicator).filter(Indicator.code == code).first()
        series.append(
            {
                "indicator_code": code,
                "indicator_name": ind.name if ind else code,
                "unit": ind.unit if ind else "",
                "data": [
                    {"country": r.country_iso3, "year": r.year, "value": r.value}
                    for r in rows
                ],
            }
        )

    return {
        "goal": goal,
        "title": goal_meta["title"],
        "country": country,
        "series": series,
    }
