import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.main import app
from app.database import Base, get_db

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
    app.dependency_overrides[get_db] = _override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()
    Base.metadata.drop_all(bind=engine)


def test_register_user(client):
    resp = client.post("/api/v1/auth/register", json={
        "email": "test@aic.africa",
        "full_name": "Test User",
        "password": "securepassword123",
    })
    assert resp.status_code == 201
    data = resp.json()
    assert data["email"] == "test@aic.africa"
    assert data["role"] == "viewer"


def test_register_duplicate_email(client):
    payload = {"email": "dup@aic.africa", "full_name": "Dup", "password": "pass123"}
    client.post("/api/v1/auth/register", json=payload)
    resp = client.post("/api/v1/auth/register", json=payload)
    assert resp.status_code == 400


def test_login_success(client):
    client.post("/api/v1/auth/register", json={
        "email": "login@aic.africa",
        "full_name": "Login User",
        "password": "mypassword",
    })
    resp = client.post("/api/v1/auth/login", json={
        "email": "login@aic.africa",
        "password": "mypassword",
    })
    assert resp.status_code == 200
    assert "access_token" in resp.json()


def test_login_wrong_password(client):
    client.post("/api/v1/auth/register", json={
        "email": "bad@aic.africa",
        "full_name": "Bad Login",
        "password": "correct",
    })
    resp = client.post("/api/v1/auth/login", json={
        "email": "bad@aic.africa",
        "password": "wrong",
    })
    assert resp.status_code == 401


def test_profile_requires_auth(client):
    resp = client.get("/api/v1/auth/profile")
    assert resp.status_code == 403


def test_profile_with_token(client):
    client.post("/api/v1/auth/register", json={
        "email": "profile@aic.africa",
        "full_name": "Profile User",
        "password": "pw123456",
    })
    login = client.post("/api/v1/auth/login", json={
        "email": "profile@aic.africa",
        "password": "pw123456",
    })
    token = login.json()["access_token"]
    resp = client.get("/api/v1/auth/profile", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200
    assert resp.json()["email"] == "profile@aic.africa"
