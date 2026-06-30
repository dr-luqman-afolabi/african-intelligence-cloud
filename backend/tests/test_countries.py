import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.main import app
from app.database import Base, get_db
from app.models.country import Country

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
    db.add(Country(iso3="NGA", iso2="NG", name="Nigeria", region="Sub-Saharan Africa"))
    db.add(Country(iso3="RWA", iso2="RW", name="Rwanda", region="Sub-Saharan Africa"))
    db.commit()
    db.close()
    app.dependency_overrides[get_db] = _override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()
    Base.metadata.drop_all(bind=engine)


def test_list_countries(client):
    resp = client.get("/api/v1/countries")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) >= 2
    iso3s = [c["iso3"] for c in data]
    assert "NGA" in iso3s
    assert "RWA" in iso3s


def test_countries_sorted_by_name(client):
    resp = client.get("/api/v1/countries")
    names = [c["name"] for c in resp.json()]
    assert names == sorted(names)
