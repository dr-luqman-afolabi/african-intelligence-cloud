from __future__ import annotations

import logging
from uuid import uuid4

from sqlalchemy.orm import Session

from app.models.survey import Survey
from app.models.survey_round import SurveyRound

logger = logging.getLogger(__name__)

# Canonical African survey programmes to seed on startup
_SEED_SURVEYS = [
    {
        "survey_id": "dhs_africa",
        "title": "Demographic and Health Surveys — Africa",
        "series": "DHS",
        "source_id": "dhs_program",
        "primary_topic": "health",
        "requires_approval": False,
        "redistribution_allowed": False,
        "microdata_available": True,
        "access_url": "https://dhsprogram.com/data/available-datasets.cfm",
        "documentation_url": "https://dhsprogram.com/methodology/",
        "tags": ["health", "fertility", "nutrition", "child_mortality"],
    },
    {
        "survey_id": "lsms_africa",
        "title": "Living Standards Measurement Study — Africa",
        "series": "LSMS",
        "source_id": "unps_lsms",
        "primary_topic": "poverty",
        "requires_approval": True,
        "redistribution_allowed": False,
        "microdata_available": True,
        "access_url": "https://microdata.worldbank.org/index.php/catalog/lsms",
        "documentation_url": "https://www.worldbank.org/en/programs/lsms",
        "tags": ["poverty", "household", "consumption", "agriculture"],
    },
    {
        "survey_id": "ipums_africa",
        "title": "IPUMS International — African Census Microdata",
        "series": "IPUMS",
        "source_id": "ipums_africa",
        "primary_topic": "demography",
        "requires_approval": True,
        "redistribution_allowed": False,
        "microdata_available": True,
        "access_url": "https://international.ipums.org/international/",
        "documentation_url": "https://international.ipums.org/international/intro.shtml",
        "tags": ["census", "demography", "population", "migration"],
    },
    {
        "survey_id": "afrobarometer",
        "title": "Afrobarometer — Public Opinion Surveys",
        "series": "AFROBAROMETER",
        "source_id": "afrobarometer",
        "primary_topic": "governance",
        "requires_approval": False,
        "redistribution_allowed": True,
        "microdata_available": True,
        "access_url": "https://www.afrobarometer.org/data/",
        "documentation_url": "https://www.afrobarometer.org/surveys-and-methods/",
        "tags": ["governance", "democracy", "public_opinion", "corruption"],
    },
    {
        "survey_id": "mics_africa",
        "title": "Multiple Indicator Cluster Surveys — Africa (UNICEF)",
        "series": "MICS",
        "source_id": "unicef_mics",
        "primary_topic": "child_welfare",
        "requires_approval": True,
        "redistribution_allowed": False,
        "microdata_available": True,
        "access_url": "https://mics.unicef.org/surveys",
        "documentation_url": "https://mics.unicef.org/methodology",
        "tags": ["children", "education", "water_sanitation", "nutrition"],
    },
    {
        "survey_id": "finscope_africa",
        "title": "FinScope — Financial Inclusion Surveys",
        "series": "FINSCOPE",
        "source_id": "finscope",
        "primary_topic": "financial_inclusion",
        "requires_approval": True,
        "redistribution_allowed": False,
        "microdata_available": False,
        "access_url": "https://www.finmark.org.za/finscope/",
        "documentation_url": "https://www.finmark.org.za/finscope/about/",
        "tags": ["financial_inclusion", "banking", "insurance", "mobile_money"],
    },
    {
        "survey_id": "lsms_isa_ethiopia_ess",
        "title": "Ethiopia Socioeconomic Survey (ESS / LSMS-ISA)",
        "series": "LSMS",
        "source_id": "wb_microdata",
        "country_iso3": "ETH",
        "primary_topic": "agriculture",
        "requires_approval": True,
        "redistribution_allowed": False,
        "microdata_available": True,
        "access_url": "https://microdata.worldbank.org/index.php/catalog/lsms",
        "documentation_url": "https://github.com/EvansSchoolPolicyAnalysisAndResearch/LSMS-Data-Dissemination",
        "tags": ["lsms-isa", "epar", "agriculture", "poverty", "household", "panel"],
    },
    {
        "survey_id": "lsms_isa_malawi_ihs",
        "title": "Malawi Integrated Household Survey / IHPS (LSMS-ISA)",
        "series": "LSMS",
        "source_id": "wb_microdata",
        "country_iso3": "MWI",
        "primary_topic": "agriculture",
        "requires_approval": True,
        "redistribution_allowed": False,
        "microdata_available": True,
        "access_url": "https://microdata.worldbank.org/index.php/catalog/lsms",
        "documentation_url": "https://github.com/EvansSchoolPolicyAnalysisAndResearch/LSMS-Data-Dissemination",
        "tags": ["lsms-isa", "epar", "agriculture", "poverty", "household", "panel"],
    },
    {
        "survey_id": "lsms_isa_nigeria_ghs",
        "title": "Nigeria General Household Survey — Panel (LSMS-ISA)",
        "series": "LSMS",
        "source_id": "wb_microdata",
        "country_iso3": "NGA",
        "primary_topic": "agriculture",
        "requires_approval": True,
        "redistribution_allowed": False,
        "microdata_available": True,
        "access_url": "https://microdata.worldbank.org/index.php/catalog/lsms",
        "documentation_url": "https://github.com/EvansSchoolPolicyAnalysisAndResearch/LSMS-Data-Dissemination",
        "tags": ["lsms-isa", "epar", "agriculture", "poverty", "household", "panel"],
    },
    {
        "survey_id": "lsms_isa_tanzania_nps",
        "title": "Tanzania National Panel Survey (NPS / LSMS-ISA)",
        "series": "LSMS",
        "source_id": "wb_microdata",
        "country_iso3": "TZA",
        "primary_topic": "agriculture",
        "requires_approval": True,
        "redistribution_allowed": False,
        "microdata_available": True,
        "access_url": "https://microdata.worldbank.org/index.php/catalog/lsms",
        "documentation_url": "https://github.com/EvansSchoolPolicyAnalysisAndResearch/LSMS-Data-Dissemination",
        "tags": ["lsms-isa", "epar", "agriculture", "poverty", "household", "panel"],
    },
    {
        "survey_id": "lsms_isa_uganda_unps",
        "title": "Uganda National Panel Survey (UNPS / LSMS-ISA)",
        "series": "LSMS",
        "source_id": "wb_microdata",
        "country_iso3": "UGA",
        "primary_topic": "agriculture",
        "requires_approval": True,
        "redistribution_allowed": False,
        "microdata_available": True,
        "access_url": "https://microdata.worldbank.org/index.php/catalog/lsms",
        "documentation_url": "https://github.com/EvansSchoolPolicyAnalysisAndResearch/LSMS-Data-Dissemination",
        "tags": ["lsms-isa", "epar", "agriculture", "poverty", "household", "panel"],
    },
    {
        "survey_id": "lsms_isa_niger_ecvma",
        "title": "Niger National Survey on Household Living Conditions and Agriculture (ECVMA / LSMS-ISA)",
        "series": "LSMS",
        "source_id": "wb_microdata",
        "country_iso3": "NER",
        "primary_topic": "agriculture",
        "requires_approval": True,
        "redistribution_allowed": False,
        "microdata_available": True,
        "access_url": "https://microdata.worldbank.org/index.php/catalog/lsms",
        "documentation_url": "https://github.com/EvansSchoolPolicyAnalysisAndResearch/LSMS-Data-Dissemination",
        "tags": ["lsms-isa", "epar", "agriculture", "poverty", "household"],
    },
    {
        "survey_id": "lsms_isa_mali_eac",
        "title": "Mali Agricultural Conjunctural Survey (EAC / LSMS-ISA)",
        "series": "LSMS",
        "source_id": "wb_microdata",
        "country_iso3": "MLI",
        "primary_topic": "agriculture",
        "requires_approval": True,
        "redistribution_allowed": False,
        "microdata_available": True,
        "access_url": "https://microdata.worldbank.org/index.php/catalog/lsms",
        "documentation_url": "https://github.com/EvansSchoolPolicyAnalysisAndResearch/LSMS-Data-Dissemination",
        "tags": ["lsms-isa", "epar", "agriculture", "poverty", "household"],
    },
    {
        "survey_id": "lsms_isa_burkinafaso_emc",
        "title": "Burkina Faso Continuous Multisector Survey (EMC / LSMS-ISA)",
        "series": "LSMS",
        "source_id": "wb_microdata",
        "country_iso3": "BFA",
        "primary_topic": "agriculture",
        "requires_approval": True,
        "redistribution_allowed": False,
        "microdata_available": True,
        "access_url": "https://microdata.worldbank.org/index.php/catalog/lsms",
        "documentation_url": "https://github.com/EvansSchoolPolicyAnalysisAndResearch/LSMS-Data-Dissemination",
        "tags": ["lsms-isa", "epar", "agriculture", "poverty", "household"],
    },
]


def seed_surveys(db: Session) -> None:
    """Idempotently seed canonical African survey programmes."""
    for data in _SEED_SURVEYS:
        existing = db.query(Survey).filter(Survey.survey_id == data["survey_id"]).first()
        if existing is None:
            db.add(Survey(id=uuid4(), **data))
    db.commit()
    logger.info("Survey registry seeded with %d programmes", len(_SEED_SURVEYS))


def list_surveys(db: Session, series: str | None = None, country_iso3: str | None = None,
                 skip: int = 0, limit: int = 100) -> list[Survey]:
    q = db.query(Survey)
    if series:
        q = q.filter(Survey.series == series.upper())
    if country_iso3:
        q = q.filter(Survey.country_iso3 == country_iso3.upper())
    return q.offset(skip).limit(limit).all()


def get_survey(db: Session, survey_id: str) -> Survey | None:
    return db.query(Survey).filter(Survey.survey_id == survey_id).first()


def list_rounds(db: Session, survey_id: str) -> list[SurveyRound]:
    return db.query(SurveyRound).filter(SurveyRound.survey_id == survey_id).all()
