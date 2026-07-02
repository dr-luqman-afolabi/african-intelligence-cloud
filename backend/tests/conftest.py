"""Shared pytest fixtures for all test modules.

Each test module that imports `client` as a fixture parameter gets a fresh
in-memory SQLite database so tests are fully isolated.
"""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.pool import StaticPool
from sqlalchemy.orm import sessionmaker

import app.database as _db_module
from app.database import Base, get_db
from app.models.country import Country
from app.models.indicator import Indicator

import os as _os
_test_db_url = _os.environ.get("DATABASE_URL", "sqlite:///:memory:")
_extra_kw = {"connect_args": {"check_same_thread": False}} if "sqlite" in _test_db_url else {}
engine = create_engine(_test_db_url, **_extra_kw)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
_db_module.engine = engine
_db_module.SessionLocal = TestingSessionLocal

from app.main import app  # import AFTER patching engine
import app.main as _main_module
_main_module.engine = engine
_main_module.SessionLocal = TestingSessionLocal


def _override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


def _seed_db():
    """Seed minimal reference data so service layers have something to search."""
    db = TestingSessionLocal()
    try:
        db.add(Country(iso3="NGA", iso2="NG", name="Nigeria", region="Sub-Saharan Africa"))
        db.add(Country(iso3="KEN", iso2="KE", name="Kenya", region="Sub-Saharan Africa"))
        db.add(Country(iso3="ZAF", iso2="ZA", name="South Africa", region="Sub-Saharan Africa"))
        db.add(
            Indicator(
                code="NY.GDP.MKTP.KD.ZG",
                name="GDP growth (annual %)",
                category="Economy",
                description="Annual percentage growth rate of GDP",
                unit="%",
                source="World Bank",
            )
        )
        db.add(
            Indicator(
                code="FP.CPI.TOTL.ZG",
                name="Inflation, consumer prices (annual %)",
                category="Economy",
                description="Consumer price inflation",
                unit="%",
                source="World Bank",
            )
        )
        db.add(
            Indicator(
                code="SL.UEM.TOTL.ZS",
                name="Unemployment, total (% of total labor force)",
                category="Labour",
                description="Share of labor force that is unemployed",
                unit="%",
                source="World Bank",
            )
        )
        db.commit()
    finally:
        db.close()


@pytest.fixture
def client():
    """Provide a TestClient backed by a fresh in-memory SQLite DB."""
    Base.metadata.create_all(bind=engine)
    _seed_db()
    app.dependency_overrides[get_db] = _override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()
    Base.metadata.drop_all(bind=engine)
