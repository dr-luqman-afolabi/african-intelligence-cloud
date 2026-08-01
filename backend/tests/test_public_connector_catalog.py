"""Public connector catalogue contract tests."""
from fastapi.testclient import TestClient


def test_connector_catalog_is_public(client: TestClient):
    response = client.get("/api/v1/connectors")

    assert response.status_code == 200
    body = response.json()
    assert isinstance(body, list)
    assert len(body) > 0
    assert {"source_id", "source_name", "connector_status"} <= set(body[0])


def test_connector_sync_remains_protected(client: TestClient):
    response = client.post("/api/v1/connectors/world_bank/sync")

    assert response.status_code in {401, 403}
