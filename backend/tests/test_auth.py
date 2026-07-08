import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.main import app
from app.database import Base, get_db

engine = create_engine(
    "sqlite:///:memory:", connect_args={"check_same_thread": False}, poolclass=StaticPool
)
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
    # The first user ever registered in a fresh DB is bootstrapped as
    # super_admin (see register_user in auth_service.py) so there's always a
    # way to approve subsequent pending users.
    assert data["role"] == "super_admin"


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


# ── Admin user management ────────────────────────────────────────────────────

def _admin_headers(client):
    """Register the bootstrap super_admin and a pending viewer; return
    (admin headers, pending user id)."""
    client.post("/api/v1/auth/register", json={
        "email": "admin@aic.africa", "full_name": "Admin", "password": "adminpw1",
    })
    pending = client.post("/api/v1/auth/register", json={
        "email": "pending@aic.africa", "full_name": "Pending", "password": "pendpw12",
    }).json()
    token = client.post("/api/v1/auth/login", json={
        "email": "admin@aic.africa", "password": "adminpw1",
    }).json()["access_token"]
    return {"Authorization": f"Bearer {token}"}, pending["id"]


def test_list_all_users_requires_admin(client):
    headers, pending_id = _admin_headers(client)
    # Approve the viewer, then use their token — must be forbidden.
    client.post(f"/api/v1/auth/approve/{pending_id}", headers=headers)
    viewer_token = client.post("/api/v1/auth/login", json={
        "email": "pending@aic.africa", "password": "pendpw12",
    }).json()["access_token"]
    resp = client.get("/api/v1/auth/users", headers={"Authorization": f"Bearer {viewer_token}"})
    assert resp.status_code == 403


def test_list_all_users(client):
    headers, _ = _admin_headers(client)
    resp = client.get("/api/v1/auth/users", headers=headers)
    assert resp.status_code == 200
    users = resp.json()
    assert len(users) == 2
    assert {u["email"] for u in users} == {"admin@aic.africa", "pending@aic.africa"}
    assert all("created_at" in u for u in users)


def test_reject_pending_user_frees_email(client):
    headers, pending_id = _admin_headers(client)
    resp = client.delete(f"/api/v1/auth/reject/{pending_id}", headers=headers)
    assert resp.status_code == 204
    # Email can register again after rejection.
    resp = client.post("/api/v1/auth/register", json={
        "email": "pending@aic.africa", "full_name": "Again", "password": "newpw123",
    })
    assert resp.status_code == 201


def test_reject_verified_user_conflicts(client):
    headers, pending_id = _admin_headers(client)
    client.post(f"/api/v1/auth/approve/{pending_id}", headers=headers)
    resp = client.delete(f"/api/v1/auth/reject/{pending_id}", headers=headers)
    assert resp.status_code == 409


def test_deactivate_blocks_login_and_activate_restores(client):
    headers, pending_id = _admin_headers(client)
    client.post(f"/api/v1/auth/approve/{pending_id}", headers=headers)

    resp = client.post(f"/api/v1/auth/users/{pending_id}/deactivate", headers=headers)
    assert resp.status_code == 200
    assert resp.json()["is_active"] is False
    login = client.post("/api/v1/auth/login", json={
        "email": "pending@aic.africa", "password": "pendpw12",
    })
    assert login.status_code == 403

    resp = client.post(f"/api/v1/auth/users/{pending_id}/activate", headers=headers)
    assert resp.json()["is_active"] is True
    login = client.post("/api/v1/auth/login", json={
        "email": "pending@aic.africa", "password": "pendpw12",
    })
    assert login.status_code == 200


def test_change_role(client):
    headers, pending_id = _admin_headers(client)
    resp = client.patch(
        f"/api/v1/auth/users/{pending_id}/role",
        json={"role": "analyst"},
        headers=headers,
    )
    assert resp.status_code == 200
    assert resp.json()["role"] == "analyst"


def test_admin_cannot_modify_self(client):
    headers, _ = _admin_headers(client)
    me = client.get("/api/v1/auth/profile", headers=headers).json()
    resp = client.post(f"/api/v1/auth/users/{me['id']}/deactivate", headers=headers)
    assert resp.status_code == 400
    resp = client.patch(f"/api/v1/auth/users/{me['id']}/role", json={"role": "viewer"}, headers=headers)
    assert resp.status_code == 400


def test_org_admin_cannot_touch_super_admin(client):
    headers, pending_id = _admin_headers(client)
    # Promote the pending user to org_admin and approve them.
    client.post(f"/api/v1/auth/approve/{pending_id}", headers=headers)
    client.patch(f"/api/v1/auth/users/{pending_id}/role", json={"role": "org_admin"}, headers=headers)
    org_token = client.post("/api/v1/auth/login", json={
        "email": "pending@aic.africa", "password": "pendpw12",
    }).json()["access_token"]
    org_headers = {"Authorization": f"Bearer {org_token}"}
    super_admin = client.get("/api/v1/auth/profile", headers=headers).json()

    resp = client.post(f"/api/v1/auth/users/{super_admin['id']}/deactivate", headers=org_headers)
    assert resp.status_code == 403
    # And an org_admin cannot grant super_admin.
    third = client.post("/api/v1/auth/register", json={
        "email": "third@aic.africa", "full_name": "Third", "password": "thirdpw1",
    }).json()
    resp = client.patch(
        f"/api/v1/auth/users/{third['id']}/role", json={"role": "super_admin"}, headers=org_headers
    )
    assert resp.status_code == 403
