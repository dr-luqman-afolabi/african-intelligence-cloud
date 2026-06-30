import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.main import app
from app.database import Base, get_db
from app.models.country import Country
from app.models.indicator import Indicator
from app.models.macro_data import MacroData

engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def _override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture
def client():
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    nga = Country(iso3="NGA", iso2="NG", name="Nigeria", region="Sub-Saharan Africa")
    ind = Indicator(code="NY.GDP.PCAP.CD", name="GDP per Capita (USD)", unit="USD", category="Growth")
    db.add_all([nga, ind])
    db.flush()
    db.add(MacroData(country_id=nga.id, indicator_id=ind.id, year=2022, value=2184.4))
    db.add(MacroData(country_id=nga.id, indicator_id=ind.id, year=2021, value=2085.8))
    db.commit()
    db.close()
    app.dependency_overrides[get_db] = _override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()
    Base.metadata.drop_all(bind=engine)


def test_get_macro_data_nga(client):
    resp = client.get("/api/v1/macro-data?country=NGA")
    assert resp.status_code == 200
    data = resp.json()
    assert data["country_iso3"] == "NGA"
    assert data["country_name"] == "Nigeria"
    assert len(data["data"]) >= 2


def test_get_macro_data_case_insensitive(client):
    resp = client.get("/api/v1/macro-data?country=nga")
    assert resp.status_code == 200


def test_get_macro_data_unknown_country(client):
    resp = client.get("/api/v1/macro-data?country=USA")
    assert resp.status_code == 404


def test_get_macro_data_missing_country_param(client):
    resp = client.get("/api/v1/macro-data")
    assert resp.status_code == 422
