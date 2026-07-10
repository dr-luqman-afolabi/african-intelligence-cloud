"""Tests for automatic boundary loading that makes spatial maps render."""
import io

import app.services.boundary_provider_service as bp


def test_adm_level_mapping():
    assert bp._adm(None) == "ADM1"
    assert bp._adm("1") == "ADM1"
    assert bp._adm(2) == "ADM2"
    assert bp._adm("ADM2") == "ADM2"
    assert bp._adm("0") == "ADM0"


def test_normalize_sets_admin_name_and_drops_geometryless():
    gj = {"features": [
        {"geometry": {"type": "Polygon", "coordinates": []}, "properties": {"shapeName": "Kigali"}},
        {"geometry": None, "properties": {"shapeName": "NoGeom"}},
    ]}
    out = bp._normalize(gj, "rwa", "ADM1")
    assert len(out["features"]) == 1
    props = out["features"][0]["properties"]
    assert props["admin_name"] == "Kigali"
    assert props["iso3"] == "RWA"
    assert "geoBoundaries" in props["source"]


def test_fetch_rejects_bad_iso3():
    assert bp.fetch_admin_boundaries(None) is None
    assert bp.fetch_admin_boundaries("XX") is None


def test_fetch_uses_cache(monkeypatch):
    calls = {"n": 0}

    class _Resp:
        def __init__(self, payload):
            self._p = payload
        def raise_for_status(self):
            pass
        def json(self):
            return self._p

    def fake_get(url, timeout=0):
        calls["n"] += 1
        if "api/current" in url:
            return _Resp({"simplifiedGeometryGeoJSON": "http://x/geo.json"})
        return _Resp({"features": [
            {"geometry": {"type": "Polygon", "coordinates": []}, "properties": {"shapeName": "Kigali"}},
        ]})

    monkeypatch.setattr(bp.requests, "get", fake_get)
    bp._CACHE.clear()
    out1 = bp.fetch_admin_boundaries("RWA", "1")
    assert out1 and out1["features"][0]["properties"]["admin_name"] == "Kigali"
    n_after_first = calls["n"]
    out2 = bp.fetch_admin_boundaries("RWA", "1")   # cached — no new HTTP calls
    assert out2 is out1
    assert calls["n"] == n_after_first


# -- End-to-end: the spatial map now renders via the automatic fallback --------

def _auth_headers(client, email="spatial_user@aic.africa"):
    client.post("/api/v1/auth/register",
                json={"email": email, "full_name": "Spatial User", "password": "pass1234"})
    r = client.post("/api/v1/auth/login", json={"email": email, "password": "pass1234"})
    return {"Authorization": f"Bearer {r.json()['access_token']}"}


def test_spatial_poverty_renders_map_via_auto_boundaries(client, monkeypatch):
    # Fake boundaries whose admin_name matches the survey's regions.
    fake = {"type": "FeatureCollection", "features": [
        {"type": "Feature", "geometry": {"type": "Polygon", "coordinates": [[[0, 0], [0, 1], [1, 1], [0, 0]]]},
         "properties": {"admin_name": "Kigali"}},
        {"type": "Feature", "geometry": {"type": "Polygon", "coordinates": [[[1, 1], [1, 2], [2, 2], [1, 1]]]},
         "properties": {"admin_name": "Huye"}},
    ]}
    import app.routers.microdata as mod
    monkeypatch.setattr(mod, "fetch_admin_boundaries", lambda iso3, admin_level=None: fake)

    headers = _auth_headers(client)
    content = b"pcexp,region\n50,Kigali\n800,Kigali\n1200,Huye\n300,Huye\n"
    up = client.post("/api/v1/microdata/upload",
                     data={"name": "Spatial HH", "country_iso3": "RWA"},
                     files=[("file", ("hh.csv", io.BytesIO(content), "text/csv"))],
                     headers=headers)
    ds_id = up.json()["id"]

    resp = client.post("/api/v1/microdata/analyze/spatial-poverty",
                       json={"dataset_id": ds_id, "geo_variable": "region",
                             "welfare_variable": "pcexp", "poverty_line": 500},
                       headers=headers)
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["geojson"] is not None
    assert len(body["geojson"]["features"]) == 2  # both regions matched onto the map
