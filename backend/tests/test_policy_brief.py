"""Tests for the AI Policy Brief generator and endpoint."""
import io

from app.services.policy_brief_service import generate_policy_brief


def _auth_headers(client, email):
    client.post("/api/v1/auth/register", json={"email": email, "full_name": "PB", "password": "pass1234"})
    r = client.post("/api/v1/auth/login", json={"email": email, "password": "pass1234"})
    return {"Authorization": f"Bearer {r.json()['access_token']}"}


def _csv_file():
    data = b"consumption,weight,region\n50,1,Kigali\n800,1,Kigali\n1200,1,Huye\n300,1,Huye\n"
    return ("file", ("hh.csv", io.BytesIO(data), "text/csv"))


# -- unit ---------------------------------------------------------------------

def test_generate_policy_brief_structure():
    result = {
        "summary_stats": {"headcount": 0.5, "poverty_gap": 0.2, "gini": 0.45},
        "tables": {"by_geography": [
            {"geo_value": "Huye", "headcount": 0.7},
            {"geo_value": "Kigali", "headcount": 0.3},
        ]},
        "interpretation_text": "test",
    }
    brief = generate_policy_brief("spatial_poverty", result, questions=["Which area is poorest?"])
    assert brief["domain"] == "poverty"
    assert brief["key_findings"] and brief["recommendations"]
    assert brief["qa"][0]["answer"].startswith("Huye")
    assert "## Recommendations" in brief["markdown"]
    assert "Questions & answers" in brief["markdown"]


def test_default_questions_when_none_supplied():
    brief = generate_policy_brief("agriculture", {"summary_stats": {"crop_yield": 12.0}, "tables": {}})
    assert len(brief["qa"]) >= 3  # defaults generated


# -- API integration ----------------------------------------------------------

def test_policy_brief_endpoint_from_poverty_job(client):
    headers = _auth_headers(client, "pb_user@aic.africa")
    up = client.post("/api/v1/microdata/upload", data={"name": "PB DS"}, files=[_csv_file()], headers=headers)
    dataset_id = up.json()["id"]
    analyze = client.post(
        "/api/v1/microdata/analyze/poverty",
        json={"dataset_id": dataset_id, "welfare_variable": "consumption", "poverty_line": 200,
              "weight_variable": "weight", "group_by": ["region"]},
        headers=headers,
    )
    job_id = analyze.json()["job_id"]

    brief = client.post(
        "/api/v1/microdata/policy-brief",
        json={"job_id": job_id, "audience": "cabinet", "questions": ["What is the overall poverty rate?"]},
        headers=headers,
    )
    assert brief.status_code == 200, brief.text
    body = brief.json()
    assert body["audience"] == "cabinet"
    assert body["key_findings"]
    assert body["qa"][0]["question"] == "What is the overall poverty rate?"
    assert "markdown" in body and body["markdown"]


def test_policy_brief_requires_ownership(client):
    owner = _auth_headers(client, "pb_owner@aic.africa")
    other = _auth_headers(client, "pb_other@aic.africa")
    up = client.post("/api/v1/microdata/upload", data={"name": "PB DS2"}, files=[_csv_file()], headers=owner)
    dataset_id = up.json()["id"]
    analyze = client.post(
        "/api/v1/microdata/analyze/poverty",
        json={"dataset_id": dataset_id, "welfare_variable": "consumption", "poverty_line": 200},
        headers=owner,
    )
    job_id = analyze.json()["job_id"]
    resp = client.post("/api/v1/microdata/policy-brief", json={"job_id": job_id}, headers=other)
    assert resp.status_code == 403
