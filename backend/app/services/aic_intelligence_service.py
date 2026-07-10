"""AIC Intelligence — turn a typed question into an explainable analysis plan.

Given a dataset's columns and the user's natural-language question, decide:
  * which analysis to run (poverty / agriculture / diversification, plain or
    spatial),
  * how to map the question to that analysis' variables,
  * what data-cleaning steps to propose.

Uses Vertex AI Gemini when available (see llm_provider); otherwise a fully
deterministic heuristic. Either way the result is a plan the user reviews and
confirms before anything runs — nothing here touches raw microdata rows.
"""
from __future__ import annotations

import json
import re
from typing import Any

from app.services import llm_provider
from app.services import data_cleaning_service as cleaning


# analysis key -> (label, frontend endpoint)
_ANALYSIS = {
    "poverty": ("Poverty & inequality", "poverty"),
    "spatial-poverty": ("Spatial poverty (map + hotspots)", "spatial-poverty"),
    "agriculture": ("Agricultural productivity", "agriculture"),
    "spatial-agriculture": ("Spatial agriculture", "spatial-agriculture"),
    "diversification": ("Livelihood diversification", "diversification"),
    "spatial-diversification": ("Spatial diversification", "spatial-diversification"),
}

_SPATIAL_WORDS = ("spatial", "map", "hotspot", "cluster", "moran", "lisa",
                  "geograph", "autocorrelat", "where are", "which region", "across region")
_AGRI_WORDS = ("yield", "crop", "fertil", "seed", "irrigat", "productiv", "farm",
               "harvest", "agricultur", "livestock", "extension")
_DIV_WORDS = ("diversif", "simpson", "shannon", "herfindahl", "crop mix", "livelihood", "income source")
_POV_WORDS = ("poverty", "poor", "welfare", "consumption", "expenditure", "gini",
              "inequality", "headcount", "fgt", "deprivation")

_WELFARE_KEYS = ("consum", "expend", "welfare", "pcexp", "totcons", "income", "expenditure")
_GEO_KEYS = ("region", "district", "province", "zone", "state", "lga", "admin", "county",
             "ward", "division", "subcounty", "area", "locality", "geo", "cluster_id")
_WEIGHT_KEYS = ("weight", "hhweight", "popweight", "sampl", "_wt", "wt_")


def _col_names(columns: list[dict[str, Any]]) -> list[str]:
    return [str(c.get("name") or c.get("variable_name") or "") for c in columns]


def _find(columns: list[dict[str, Any]], keys: tuple[str, ...]) -> str | None:
    """Return the best-matching column name for any of the keyword stems."""
    best = None
    best_rank = 1e9
    for c in columns:
        name = str(c.get("name") or c.get("variable_name") or "")
        label = str(c.get("label") or c.get("variable_label") or "")
        hay = f"{name} {label}".lower()
        for i, k in enumerate(keys):
            if k in hay:
                # earlier keyword + shorter name = stronger match
                rank = i * 100 + len(name)
                if rank < best_rank:
                    best, best_rank = name, rank
                break
    return best


def _pick_analysis(q: str) -> tuple[str, bool]:
    ql = q.lower()
    spatial = any(w in ql for w in _SPATIAL_WORDS)
    if any(w in ql for w in _DIV_WORDS):
        domain = "diversification"
    elif any(w in ql for w in _AGRI_WORDS):
        domain = "agriculture"
    else:
        domain = "poverty"  # default
    key = f"spatial-{domain}" if spatial else domain
    return key, spatial


def _extract_poverty_line(q: str) -> float | None:
    # "$2.15", "poverty line of 300", "line 1.90", "at 2.15 a day"
    m = re.search(r"(?:poverty\s*line|line|threshold|\$|at)\D{0,12}?(\d+(?:\.\d+)?)", q.lower())
    if m:
        try:
            return float(m.group(1))
        except ValueError:
            return None
    return None


def _heuristic_plan(question: str, columns: list[dict[str, Any]]) -> dict[str, Any]:
    analysis, spatial = _pick_analysis(question)
    domain = analysis.replace("spatial-", "")
    label, endpoint = _ANALYSIS[analysis]

    welfare = _find(columns, _WELFARE_KEYS)
    geo = _find(columns, _GEO_KEYS)
    weight = _find(columns, _WEIGHT_KEYS)
    warnings: list[str] = []
    needs_clar = False
    clar = None

    params: dict[str, Any] = {}
    targets: list[str] = []

    if domain == "poverty":
        if not welfare:
            needs_clar = True
            clar = "I couldn't find a welfare/consumption column — which column measures household welfare?"
            welfare = welfare or (_col_names(columns)[0] if columns else "consumption")
        line = _extract_poverty_line(question)
        if line is None:
            line = 2.15
            warnings.append("No poverty line stated — assumed 2.15. Edit it if your welfare is in local currency.")
        params["welfare_variable"] = welfare
        params["poverty_line"] = line
        targets = [welfare]
        if weight:
            params["weight_variable"] = weight
        if spatial:
            params["geo_variable"] = geo or ""
            if not geo:
                warnings.append("No geographic column detected for the map — pick one to enable hotspots.")
        elif geo:
            params["geography_variable"] = geo

    elif domain == "agriculture":
        if spatial:
            params["geo_variable"] = geo or ""
            if not geo:
                warnings.append("No geographic column detected — pick one to map agriculture by area.")
        elif geo:
            params["geography_variable"] = geo
        if weight:
            params["weight_variable"] = weight
        warnings.append("Agriculture uses this dataset's saved variable mappings (yield, inputs, etc.).")
        targets = [c for c in [weight] if c]

    else:  # diversification
        if spatial:
            params["geo_variable"] = geo or ""
            if not geo:
                warnings.append("No geographic column detected — pick one to map diversification by area.")
        if weight:
            params["weight_variable"] = weight
        warnings.append("Diversification auto-detects crop/income/livelihood columns unless you specify them.")

    cleaning_steps = cleaning.plan_cleaning(
        _as_df_stub(columns), target_columns=targets, free_text=question,
    )

    rationale = (
        f"Matched your question to a {label.lower()} analysis"
        + (f", mapping welfare to '{welfare}'" if domain == "poverty" and welfare else "")
        + (f" and geography to '{geo}'" if spatial and geo else "")
        + "."
    )
    return {
        "analysis": analysis,
        "analysis_label": label,
        "endpoint": endpoint,
        "parameters": params,
        "cleaning_steps": [s if isinstance(s, dict) else s for s in cleaning_steps],
        "rationale": rationale,
        "warnings": warnings,
        "engine": "heuristic",
        "needs_clarification": needs_clar,
        "clarification": clar,
    }


def _as_df_stub(columns: list[dict[str, Any]]):
    import pandas as pd
    # Build an empty typed frame so dtype checks behave.
    data = {}
    for c in columns:
        name = str(c.get("name") or c.get("variable_name") or "")
        dtype = str(c.get("dtype") or c.get("inferred_dtype") or "object").lower()
        if any(t in dtype for t in ("int", "float", "num", "double")):
            data[name] = pd.Series([], dtype="float64")
        else:
            data[name] = pd.Series([], dtype="object")
    return pd.DataFrame(data)


def _gemini_plan(question: str, columns: list[dict[str, Any]]) -> dict[str, Any] | None:
    col_desc = ", ".join(
        f"{c.get('name') or c.get('variable_name')}"
        + (f" ({c.get('label') or c.get('variable_label')})" if (c.get('label') or c.get('variable_label')) else "")
        for c in columns[:120]
    )
    prompt = f"""You are AIC Intelligence, a survey-microdata analyst for African policy data.
Choose ONE analysis for the user's question and map it to the dataset's columns.
Valid analyses: {", ".join(_ANALYSIS.keys())}.
Dataset columns: {col_desc}

Return ONLY a JSON object:
{{
  "analysis": one of the valid analyses,
  "parameters": {{ analysis params using EXACT column names, e.g. welfare_variable, poverty_line (number), weight_variable, geo_variable, geography_variable }},
  "rationale": "one sentence",
  "warnings": ["..."],
  "needs_clarification": false,
  "clarification": null
}}
User question: {json.dumps(question)}"""
    raw = llm_provider.generate_json(prompt)
    if not raw or not isinstance(raw, dict):
        return None
    analysis = str(raw.get("analysis", "")).strip()
    if analysis not in _ANALYSIS:
        return None
    label, endpoint = _ANALYSIS[analysis]
    params = raw.get("parameters") or {}
    if not isinstance(params, dict):
        params = {}
    params.pop("dataset_id", None)
    targets = [v for k, v in params.items() if k in ("welfare_variable", "geography_variable", "geo_variable") and isinstance(v, str)]
    cleaning_steps = cleaning.plan_cleaning(_as_df_stub(columns), target_columns=targets, free_text=question)
    return {
        "analysis": analysis,
        "analysis_label": label,
        "endpoint": endpoint,
        "parameters": params,
        "cleaning_steps": cleaning_steps,
        "rationale": str(raw.get("rationale") or f"Selected {label}."),
        "warnings": list(raw.get("warnings") or []),
        "engine": "gemini",
        "needs_clarification": bool(raw.get("needs_clarification", False)),
        "clarification": raw.get("clarification"),
    }


def build_plan(question: str, columns: list[dict[str, Any]]) -> dict[str, Any]:
    """Return an analysis plan dict. Tries Gemini, falls back to heuristic."""
    if llm_provider.is_available():
        try:
            plan = _gemini_plan(question, columns)
            if plan is not None:
                return plan
        except Exception:
            pass
    return _heuristic_plan(question, columns)
