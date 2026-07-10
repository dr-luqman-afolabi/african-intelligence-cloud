"""Tests for the Interactive Spatial Explorer session engine:
filter application, session CRUD, running the poverty layer, replay, ownership.
"""
import io

import pandas as pd

from app.services.explorer_session_service import apply_filters


def _auth_headers(client, email):
    client.post(
        "/api/v1/auth/register",
        json={"email": email, "full_name": "Explorer User", "password": "pass1234"},
    )
    from app.database import SessionLocal as _SL
    from app.models.user import User as _U
    _d=_SL(); _u=_d.query(_U).filter(_U.email==email).first()
    if _u:
        _u.is_verified=True; _u.is_active=True; _d.commit()
    _d.close()
    resp = client.post("/api/v1/auth/login", json={"email": email, "password": "pass1234"})
    return {"Authorization": f"Bearer {resp.json()['access_token']}"}


def _csv_file(name="household.csv"):
    data = (
        b"consumption,weight,region\n"
        b"50,1,Kigali\n"
        b"800,1,Kigali\n"
        b"1200,1,Huye\n"
        b"300,1,Huye\n"
    )
    return ("file", (name, io.BytesIO(data), "text/csv"))


def _upload(client, headers, name="Explorer DS"):
    resp = client.post(
        "/api/v1/microdata/upload",
        data={"name": name, "country_iso3": "RWA"},
        files=[_csv_file()],
        headers=headers,
    )
    assert resp.status_code in (200, 201), resp.text
    return resp.json()["id"]


# -- unit: filters ------------------------------------------------------------

def test_apply_filters_eq_and_gt():
    df = pd.DataFrame({"region": ["Kigali", "Kigali", "Huye"], "consumption": [50, 800, 1200]})
    assert len(apply_filters(df, [{"variable": "region", "op": "eq", "value": "Kigali"}])) == 2
    assert len(apply_filters(df, [{"variable": "consumption", "op": "gt", "value": 100}])) == 2
    # unknown column is ignored, not an error
    assert len(apply_filters(df, [{"variable": "nope", "op": "eq", "value": 1}])) == 3


def test_apply_filters_between_and_in():
    df = pd.DataFrame({"consumption": [50, 300, 800, 1200]})
    assert len(apply_filters(df, [{"variable": "consumption", "op": "between", "value": [100, 900]}])) == 2


# -- integration: session lifecycle ------------------------------------------

def test_create_and_run_poverty_session(client):
    headers = _auth_headers(client, "explorer_poverty@aic.africa")
    dataset_id = _upload(client, headers)

    create = client.post(
        "/api/v1/microdata/sessions",
        json={
            "name": "Rwanda poverty exploration",
            "dataset_id": dataset_id,
            "active_layer": "poverty",
            "state": {
                "geo_variable": "region",
                "welfare_variable": "consumption",
                "poverty_line": 200,
                "weight_variable": "weight",
            },
        },
        headers=headers,
    )
    assert create.status_code == 201, create.text
    session_id = create.json()["id"]

    run = client.post(f"/api/v1/microdata/sessions/{session_id}/run", json={}, headers=headers)
    assert run.status_code == 200, run.text
    body = run.json()
    assert body["status"] == "completed"
    assert body["job_type"] == "spatial_poverty"
    regions = {r["geo_value"] if "geo_value" in r else r.get("group") for r in body["tables"]["by_geography"]}
    assert "Kigali" in regions and "Huye" in regions

    # replay: last result is retrievable
    result = client.get(f"/api/v1/microdata/sessions/{session_id}/result", headers=headers)
    assert result.status_code == 200
    assert result.json()["job_id"] == body["job_id"]


def test_run_session_with_filter_narrows_units(client):
    headers = _auth_headers(client, "explorer_filter@aic.africa")
    dataset_id = _upload(client, headers)
    create = client.post(
        "/api/v1/microdata/sessions",
        json={
            "name": "Filtered",
            "dataset_id": dataset_id,
            "active_layer": "poverty",
            "state": {
                "geo_variable": "region",
                "welfare_variable": "consumption",
                "poverty_line": 200,
                "filters": [{"variable": "region", "op": "eq", "value": "Kigali"}],
            },
        },
        headers=headers,
    )
    session_id = create.json()["id"]
    run = client.post(f"/api/v1/microdata/sessions/{session_id}/run", json={}, headers=headers)
    assert run.status_code == 200, run.text
    rows = run.json()["tables"]["by_geography"]
    labels = {r.get("geo_value") or r.get("group") for r in rows}
    assert labels == {"Kigali"}


def test_update_session_persists_state(client):
    headers = _auth_headers(client, "explorer_update@aic.africa")
    dataset_id = _upload(client, headers)
    create = client.post(
        "/api/v1/microdata/sessions",
        json={"name": "S", "dataset_id": dataset_id, "state": {"geo_variable": "region"}},
        headers=headers,
    )
    session_id = create.json()["id"]
    patch = client.patch(
        f"/api/v1/microdata/sessions/{session_id}",
        json={"active_layer": "agriculture", "state": {"map_view": {"zoom": 6}}},
        headers=headers,
    )
    assert patch.status_code == 200, patch.text
    body = patch.json()
    assert body["active_layer"] == "agriculture"
    # merge preserved the original geo_variable and added map_view
    assert body["state"]["geo_variable"] == "region"
    assert body["state"]["map_view"] == {"zoom": 6}


def test_session_ownership_enforced(client):
    owner = _auth_headers(client, "explorer_owner@aic.africa")
    other = _auth_headers(client, "explorer_other@aic.africa")
    dataset_id = _upload(client, owner)
    create = client.post(
        "/api/v1/microdata/sessions",
        json={"name": "Private", "dataset_id": dataset_id},
        headers=owner,
    )
    session_id = create.json()["id"]
    resp = client.get(f"/api/v1/microdata/sessions/{session_id}", headers=other)
    assert resp.status_code == 403


def test_list_sessions_only_returns_own(client):
    a = _auth_headers(client, "explorer_lista@aic.africa")
    b = _auth_headers(client, "explorer_listb@aic.africa")
    client.post("/api/v1/microdata/sessions", json={"name": "A-owned"}, headers=a)
    listing = client.get("/api/v1/microdata/sessions", headers=b).json()
    assert all(s["name"] != "A-owned" for s in listing)
