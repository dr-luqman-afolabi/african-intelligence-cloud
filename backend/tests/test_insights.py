from app.services import insights_service


def _payload(action="interpret"):
    pts = [{"year": 2015, "value": 2.0}, {"year": 2016, "value": 2.5},
           {"year": 2017, "value": 2.2}, {"year": 2018, "value": 3.0}]
    return {"action": action, "title": "Test yield", "metric": "yield",
            "series": [{"label": "Nigeria — Maize", "country": "Nigeria", "crop": "Maize",
                        "units": "Yield (t/ha)", "points": pts}]}


def test_stats_math():
    out = insights_service.generate(_payload("interpret"))
    st = out["stats"][0]
    assert st["start_year"] == 2015 and st["end_year"] == 2018
    assert st["start_value"] == 2.0 and st["end_value"] == 3.0
    assert st["pct_change"] == 50.0          # (3-2)/2*100
    assert st["peak_year"] == 2018 and st["peak_value"] == 3.0
    assert st["trough_year"] == 2015 and st["trough_value"] == 2.0
    assert st["direction"] == "increased"


def test_interpret_heuristic_mentions_numbers(monkeypatch):
    monkeypatch.setattr(insights_service.llm_provider, "generate_json", lambda *a, **k: None)
    out = insights_service.generate(_payload("interpret"))
    assert out["source"] == "heuristic"
    assert "50.0%" in out["insight"]
    assert "2018" in out["insight"]


def test_recommend_returns_list(monkeypatch):
    monkeypatch.setattr(insights_service.llm_provider, "generate_json", lambda *a, **k: None)
    out = insights_service.generate(_payload("recommend"))
    assert out["action"] == "recommend"
    assert len(out["recommendations"]) >= 1
    assert any("AI-generated" in r for r in out["recommendations"])


def test_llm_used_when_available(monkeypatch):
    monkeypatch.setattr(insights_service.llm_provider, "generate_json",
                        lambda *a, **k: {"insight": "Model says up.", "recommendations": []})
    out = insights_service.generate(_payload("interpret"))
    assert out["source"] == "llm"
    assert out["insight"] == "Model says up."


def test_no_causal_fabrication_guardrail_present():
    assert "Do NOT invent causes" in insights_service._GUARDRAIL


def test_empty_series():
    out = insights_service.generate({"action": "interpret", "series": []})
    assert out["stats"] == []
