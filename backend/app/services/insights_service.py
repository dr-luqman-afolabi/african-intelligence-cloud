"""AIC AI Insights — grounded interpretation of a plotted series.

Design principle: the numbers are computed deterministically here (percent
change, CAGR, peak/trough, trend). The language model only *phrases* those
facts; it is explicitly forbidden from inventing causal drivers or figures that
are not in the data (no "fertilizer explains 42%" unless such a number was
supplied). When the model is unavailable, a heuristic composer produces the
same facts in plain prose, so the feature always works.
"""
from __future__ import annotations

import logging
from typing import Any

from app.services import harveststat_service, llm_provider

logger = logging.getLogger(__name__)

# Vertex AI calls can block for many seconds on a cold SDK init or a slow/errored
# backend, which starves the Cloud Run worker and produces 503s. Bound every LLM
# call to a few seconds on a background thread; on timeout we fall back to the
# deterministic heuristic so the endpoint always responds fast.
_LLM_TIMEOUT_S = 6.0

# Persistent pool: we must NOT use a `with ThreadPoolExecutor()` block, because
# its __exit__ calls shutdown(wait=True) and would block until the (possibly
# slow) Vertex call finishes — defeating the timeout and starving the worker.
# With a persistent pool we abandon the future on timeout and return at 6s.
import concurrent.futures as _futures

_LLM_POOL = _futures.ThreadPoolExecutor(max_workers=4, thread_name_prefix="insights-llm")


def _bounded_llm(prompt: str):
    try:
        fut = _LLM_POOL.submit(llm_provider.generate_json, prompt)
        return fut.result(timeout=_LLM_TIMEOUT_S)
    except Exception as exc:  # TimeoutError or any LLM failure -> heuristic
        logger.info("insights LLM skipped (%s); using heuristic", type(exc).__name__)
        return None

ACTIONS = ("interpret", "explain", "recommend", "compare")


def _series_stats(s: dict[str, Any]) -> dict[str, Any] | None:
    pts = [p for p in s.get("points", []) if p.get("value") is not None]
    if len(pts) < 2:
        return None
    pts = sorted(pts, key=lambda p: p["year"])
    y0, v0 = pts[0]["year"], float(pts[0]["value"])
    y1, v1 = pts[-1]["year"], float(pts[-1]["value"])
    peak = max(pts, key=lambda p: p["value"])
    trough = min(pts, key=lambda p: p["value"])
    pct = ((v1 - v0) / v0 * 100.0) if v0 else None
    span = y1 - y0
    cagr = (((v1 / v0) ** (1.0 / span) - 1.0) * 100.0) if (v0 > 0 and span > 0) else None
    direction = "increased" if v1 > v0 else "decreased" if v1 < v0 else "was flat"
    return {
        "label": s.get("label"), "units": s.get("units"),
        "start_year": y0, "end_year": y1,
        "start_value": round(v0, 3), "end_value": round(v1, 3),
        "pct_change": round(pct, 1) if pct is not None else None,
        "cagr_pct": round(cagr, 2) if cagr is not None else None,
        "peak_year": peak["year"], "peak_value": round(float(peak["value"]), 3),
        "trough_year": trough["year"], "trough_value": round(float(trough["value"]), 3),
        "n_points": len(pts), "direction": direction,
    }


def _heuristic_narrative(title: str, stats: list[dict[str, Any]]) -> str:
    parts = []
    for st in stats:
        chg = f"{abs(st['pct_change']):.1f}%" if st["pct_change"] is not None else "an unclear amount"
        cagr = f" ({st['cagr_pct']:.2f}%/yr)" if st["cagr_pct"] is not None else ""
        line = (f"{st['label']} {st['direction']} by {chg}{cagr} between {st['start_year']} "
                f"({st['start_value']} {st['units']}) and {st['end_year']} "
                f"({st['end_value']} {st['units']}). It peaked in {st['peak_year']} "
                f"at {st['peak_value']} and was lowest in {st['trough_year']} "
                f"at {st['trough_value']}.")
        parts.append(line)
    return " ".join(parts)


def _heuristic_recommendations(stats: list[dict[str, Any]]) -> list[str]:
    recs: list[str] = []
    for st in stats:
        lbl = st["label"]
        if st["direction"] == "decreased":
            recs.append(f"{lbl}: the downward trend warrants investigating input access "
                        f"(seed, fertilizer), extension coverage and climate exposure in the affected areas.")
        elif st["cagr_pct"] is not None and st["cagr_pct"] < 1.0:
            recs.append(f"{lbl}: growth is slow (~{st['cagr_pct']:.2f}%/yr); targeted productivity "
                        f"programmes (improved varieties, irrigation, mechanisation) could accelerate it.")
        else:
            recs.append(f"{lbl}: gains are positive — sustaining them means protecting the drivers "
                        f"behind them and monitoring for weather or price shocks.")
    recs.append("These are AI-generated starting points, not causal findings — validate against "
                "district data and field evidence before acting.")
    return recs


def _facts_block(title: str, metric: str, stats: list[dict[str, Any]]) -> str:
    lines = [f"Chart title: {title}", f"Metric: {metric}", "Series facts (the ONLY numbers you may use):"]
    for st in stats:
        lines.append(
            f"- {st['label']}: {st['start_value']} {st['units']} in {st['start_year']} -> "
            f"{st['end_value']} in {st['end_year']} "
            f"({'+' if (st['pct_change'] or 0) >= 0 else ''}{st['pct_change']}% total"
            f"{', ' + str(st['cagr_pct']) + '%/yr' if st['cagr_pct'] is not None else ''}); "
            f"peak {st['peak_value']} in {st['peak_year']}, low {st['trough_value']} in {st['trough_year']}."
        )
    return "\n".join(lines)


_GUARDRAIL = (
    "You are AIC's agricultural data analyst. Interpret ONLY the numbers given. "
    "Do NOT invent causes, drivers, percentages, districts, or facts that are not "
    "in the data. If a cause is unknown, say it requires further analysis. "
    "Be concise, neutral and policy-relevant. Return JSON."
)


def generate(payload: dict[str, Any]) -> dict[str, Any]:
    action = (payload.get("action") or "interpret").lower()
    if action not in ACTIONS:
        action = "interpret"
    title = payload.get("title") or "Selected series"
    metric = payload.get("metric") or ""
    raw_series = payload.get("series") or []

    stats = [s for s in (_series_stats(x) for x in raw_series) if s]
    if not stats:
        return {"action": action, "insight": "Not enough data points to interpret this selection.",
                "stats": [], "recommendations": [], "source": "none"}

    if action == "compare":
        return _compare(stats, raw_series)

    facts = _facts_block(title, metric, stats)
    llm_out = None
    if action == "recommend":
        prompt = (f"{_GUARDRAIL}\n\n{facts}\n\n"
                  "Return {\"insight\": <2-sentence summary>, \"recommendations\": [<3-5 short, "
                  "generic, evidence-informed intervention ideas tied to the observed trend; "
                  "each must be clearly a suggestion, not a proven cause>]}.")
    else:
        detail = "one short paragraph" if action == "interpret" else "two short paragraphs with more nuance"
        prompt = (f"{_GUARDRAIL}\n\n{facts}\n\n"
                  f"Write {detail} interpreting the trend(s). "
                  "Return {\"insight\": <text>, \"recommendations\": []}.")
    llm_out = _bounded_llm(prompt)

    if llm_out and isinstance(llm_out.get("insight"), str) and llm_out["insight"].strip():
        insight = llm_out["insight"].strip()
        recs = llm_out.get("recommendations") or []
        recs = [r for r in recs if isinstance(r, str)]
        if action == "recommend" and not recs:
            recs = _heuristic_recommendations(stats)
        source = "llm"
    else:
        insight = _heuristic_narrative(title, stats)
        recs = _heuristic_recommendations(stats) if action == "recommend" else []
        source = "heuristic"

    return {"action": action, "insight": insight, "recommendations": recs,
            "stats": stats, "source": source}


def _compare(stats: list[dict[str, Any]], raw_series: list[dict[str, Any]]) -> dict[str, Any]:
    """Suggest peer countries that grow the same crop(s). No fabricated numbers."""
    crops = {s.get("crop") for s in raw_series if s.get("crop")}
    countries = {s.get("country") for s in raw_series if s.get("country")}
    peers: dict[str, list[str]] = {}
    try:
        meta = harveststat_service.get_meta()
        cbc = meta.get("crops_by_country", {})
        for crop in crops:
            same = [c for c, cl in cbc.items() if crop in (cl or []) and c not in countries]
            if same:
                peers[crop] = sorted(same)
    except Exception as exc:  # pragma: no cover
        logger.info("compare peers failed: %s", exc)
    insight = ("Countries below grow the same crop and can be compared directly in the "
               "Crop Statistics explorer by adding them as extra lines.")
    if not peers:
        insight = "Add more countries in the Crop Statistics explorer to compare directly."
    return {"action": "compare", "insight": insight, "peers": peers,
            "stats": stats, "recommendations": [], "source": "catalog"}
