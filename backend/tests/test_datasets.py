"""Tests for Sprint 2: Dataset upload, list, detail, profile, delete endpoints."""
import io
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
def client(tmp_path, monkeypatch):
    # Point storage at a temp dir so tests never touch the real filesystem
    monkeypatch.setenv("UPLOAD_DIR", str(tmp_path))
    monkeypatch.setenv("STORAGE_BACKEND", "local")

    # Reset settings singleton so env changes take effect
    from app.config import get_settings
    get_settings.cache_clear()

    Base.metadata.create_all(bind=engine)
    app.dependency_overrides[get_db] = _override_get_db

    with TestClient(app) as c:
        yield c

    app.dependency_overrides.clear()
    Base.metadata.drop_all(bind=engine)

    # Re-clear so subsequent tests start clean
    get_settings.cache_clear()


def _register_and_login(client, email="ds@aic.africa"):
    client.post("/api/v1/auth/register", json={
        "email": email, "full_name": "DS User", "password": "pass1234",
    })
    resp = client.post("/api/v1/auth/login", json={"email": email, "password": "pass1234"})
    return resp.json()["access_token"]


def _auth(token):
    return {"Authorization": f"Bearer {token}"}


def _csv_file(name="data.csv", content=b"a,b,c\n1,2,3\n4,5,6\n"):
    return ("file", (name, io.BytesIO(content), "text/csv"))


# ── Authentication guards ────────────────────────────────────────────────────

def test_upload_requires_auth(client):
    resp = client.post("/api/v1/datasets/upload", data={"name": "x"}, files=[_csv_file()])
    assert resp.status_code == 403


def test_list_requires_auth(client):
    resp = client.get("/api/v1/datasets")
    assert resp.status_code == 403


def test_get_requires_auth(client):
    resp = client.get("/api/v1/datasets/00000000-0000-0000-0000-000000000001")
    assert resp.status_code == 403


def test_profile_requires_auth(client):
    resp = client.post("/api/v1/datasets/00000000-0000-0000-0000-000000000001/profile")
    assert resp.status_code == 403


def test_delete_requires_auth(client):
    resp = client.delete("/api/v1/datasets/00000000-0000-0000-0000-000000000001")
    assert resp.status_code == 403


# ── Upload ───────────────────────────────────────────────────────────────────

def test_upload_csv(client):
    token = _register_and_login(client)
    resp = client.post(
        "/api/v1/datasets/upload",
        data={"name": "My CSV", "privacy": "private"},
        files=[_csv_file()],
        headers=_auth(token),
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["name"] == "My CSV"
    assert data["file_extension"] == "csv"
    assert data["status"] == "uploaded"
    assert data["privacy"] == "private"


def test_upload_invalid_extension(client):
    token = _register_and_login(client)
    resp = client.post(
        "/api/v1/datasets/upload",
        data={"name": "Bad", "privacy": "private"},
        files=[("file", ("data.txt", io.BytesIO(b"hello"), "text/plain"))],
        headers=_auth(token),
    )
    assert resp.status_code == 422


def test_upload_invalid_privacy(client):
    token = _register_and_login(client)
    resp = client.post(
        "/api/v1/datasets/upload",
        data={"name": "Bad", "privacy": "unknown"},
        files=[_csv_file()],
        headers=_auth(token),
    )
    assert resp.status_code == 422


def test_upload_with_tags(client):
    token = _register_and_login(client)
    resp = client.post(
        "/api/v1/datasets/upload",
        data={"name": "Tagged", "privacy": "public", "tags": "africa,economy"},
        files=[_csv_file()],
        headers=_auth(token),
    )
    assert resp.status_code == 201
    assert resp.json()["privacy"] == "public"


# ── List ─────────────────────────────────────────────────────────────────────

def test_list_empty(client):
    token = _register_and_login(client)
    resp = client.get("/api/v1/datasets", headers=_auth(token))
    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] == 0
    assert data["items"] == []


def test_list_returns_own_datasets(client):
    token = _register_and_login(client)
    client.post(
        "/api/v1/datasets/upload",
        data={"name": "DS1", "privacy": "private"},
        files=[_csv_file()],
        headers=_auth(token),
    )
    resp = client.get("/api/v1/datasets", headers=_auth(token))
    assert resp.status_code == 200
    assert resp.json()["total"] == 1


def test_list_pagination(client):
    token = _register_and_login(client)
    for i in range(3):
        client.post(
            "/api/v1/datasets/upload",
            data={"name": f"DS{i}", "privacy": "private"},
            files=[_csv_file()],
            headers=_auth(token),
        )
    resp = client.get("/api/v1/datasets?page=1&page_size=2", headers=_auth(token))
    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] == 3
    assert len(data["items"]) == 2


# ── Get detail ───────────────────────────────────────────────────────────────

def test_get_dataset_detail(client):
    token = _register_and_login(client)
    upload = client.post(
        "/api/v1/datasets/upload",
        data={"name": "Detail DS", "privacy": "private"},
        files=[_csv_file()],
        headers=_auth(token),
    ).json()
    resp = client.get(f"/api/v1/datasets/{upload['id']}", headers=_auth(token))
    assert resp.status_code == 200
    data = resp.json()
    assert data["id"] == upload["id"]
    assert "columns" in data
    assert "profile" in data


def test_get_dataset_not_found(client):
    token = _register_and_login(client)
    resp = client.get(
        "/api/v1/datasets/00000000-0000-0000-0000-000000000099",
        headers=_auth(token),
    )
    assert resp.status_code == 404


def test_get_private_dataset_other_user_forbidden(client):
    token1 = _register_and_login(client, email="user1@aic.africa")
    token2 = _register_and_login(client, email="user2@aic.africa")

    upload = client.post(
        "/api/v1/datasets/upload",
        data={"name": "Private", "privacy": "private"},
        files=[_csv_file()],
        headers=_auth(token1),
    ).json()

    resp = client.get(f"/api/v1/datasets/{upload['id']}", headers=_auth(token2))
    assert resp.status_code == 403


def test_get_public_dataset_other_user_allowed(client):
    token1 = _register_and_login(client, email="pub1@aic.africa")
    token2 = _register_and_login(client, email="pub2@aic.africa")

    upload = client.post(
        "/api/v1/datasets/upload",
        data={"name": "Public DS", "privacy": "public"},
        files=[_csv_file()],
        headers=_auth(token1),
    ).json()

    resp = client.get(f"/api/v1/datasets/{upload['id']}", headers=_auth(token2))
    assert resp.status_code == 200


# ── Profile ──────────────────────────────────────────────────────────────────

def test_trigger_profiling(client):
    token = _register_and_login(client)
    upload = client.post(
        "/api/v1/datasets/upload",
        data={"name": "Profile Me", "privacy": "private"},
        files=[_csv_file()],
        headers=_auth(token),
    ).json()

    resp = client.post(f"/api/v1/datasets/{upload['id']}/profile", headers=_auth(token))
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "profiling"
    assert data["dataset_id"] == upload["id"]


def test_trigger_profiling_not_found(client):
    token = _register_and_login(client)
    resp = client.post(
        "/api/v1/datasets/00000000-0000-0000-0000-000000000099/profile",
        headers=_auth(token),
    )
    assert resp.status_code == 404


def test_trigger_profiling_already_in_progress(client):
    token = _register_and_login(client)
    upload = client.post(
        "/api/v1/datasets/upload",
        data={"name": "Double", "privacy": "private"},
        files=[_csv_file()],
        headers=_auth(token),
    ).json()

    client.post(f"/api/v1/datasets/{upload['id']}/profile", headers=_auth(token))
    resp = client.post(f"/api/v1/datasets/{upload['id']}/profile", headers=_auth(token))
    assert resp.status_code == 409


# ── Delete ───────────────────────────────────────────────────────────────────

def test_delete_dataset(client):
    token = _register_and_login(client)
    upload = client.post(
        "/api/v1/datasets/upload",
        data={"name": "Delete Me", "privacy": "private"},
        files=[_csv_file()],
        headers=_auth(token),
    ).json()

    resp = client.delete(f"/api/v1/datasets/{upload['id']}", headers=_auth(token))
    assert resp.status_code == 204

    # Confirm gone
    resp = client.get(f"/api/v1/datasets/{upload['id']}", headers=_auth(token))
    assert resp.status_code == 404


def test_delete_other_users_dataset_forbidden(client):
    token1 = _register_and_login(client, email="del1@aic.africa")
    token2 = _register_and_login(client, email="del2@aic.africa")

    upload = client.post(
        "/api/v1/datasets/upload",
        data={"name": "Not Yours", "privacy": "public"},
        files=[_csv_file()],
        headers=_auth(token1),
    ).json()

    resp = client.delete(f"/api/v1/datasets/{upload['id']}", headers=_auth(token2))
    assert resp.status_code == 403


def test_delete_not_found(client):
    token = _register_and_login(client)
    resp = client.delete(
        "/api/v1/datasets/00000000-0000-0000-0000-000000000099",
        headers=_auth(token),
    )
    assert resp.status_code == 404
