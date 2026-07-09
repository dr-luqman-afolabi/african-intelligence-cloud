"""AI Policy Brief generator.

Turns a completed microdata analysis result (poverty / agriculture /
diversification, plain or spatial) into a structured, download-ready policy
brief: executive summary, key findings, recommendations, a data-grounded
Q&A section, and an assembled Markdown document.

The generator is heuristic and fully data-grounded — it reads only the
aggregated ``summary_stats`` / ``tables`` / ``interpretation_text`` that the
analysis already produced, so it needs no external LLM or API key and never
touches raw microdata. It mirrors the existing ai-interpret approach.
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any


_DOMAIN_BY_JOBTYPE = {
    "poverty": "poverty",
    "spatial_poverty": "poverty",
    "agriculture": "agriculture",
    "spatial_agriculture": "agriculture",
    "diversification": "diversification",
    "spatial_diversification": "diversification",
}

_DOMAIN_TITLE = {
    "poverty": "Poverty & Welfare",
    "agriculture": "Agricultural Productivity",
    "diversification": "Livelihood Diversification",
}

# Primary metric per domain, used for ranking geographic units in the brief.
_VALUE_FIELD = {
    "poverty": "poverty_headcount",
    "agriculture": "crop_yield",
    "diversification": "crop_simpson_index",
}
# Fallback keys as they appear in non-merged "by_geography" rows.
_ROW_VALUE_KEYS = {
    "poverty": ["poverty_headcount", "headcount"],
    "agriculture": ["crop_yield"],
    "diversification": ["crop_simpson_index", "simpson_index"],
}


def _pct(v: Any) -> str:
    return f"{v * 100:.1f}%" if isinstance(v, (int, float)) else "—"


def _num(v: Any, nd: int = 2) -> str:
    return f"{v:.{nd}f}" if isinstance(v, (int, float)) else "—"


def _row_value(row: dict, domain: str) -> float | None:
    for k in _ROW_VALUE_KEYS.get(domain, []):
        if isinstance(row.get(k), (int, float)):
            return float(row[k])
    return None


def _row_label(row: dict) -> str:
    return str(row.get("admin_name") or row.get("geo_value") or row.get("group") or "unit")


def _ranked_units(result: dict, domain: str) -> list[dict]:
    tables = result.get("tables") or {}
    rows = tables.get("by_geography")
    if not isinstance(rows, list):
        # fall back to any grouped list in tables
        for k, v in tables.items():
            if k not in ("overall",) and isinstance(v, list) and v and isinstance(v[0], dict):
                rows = v
                break
    if not isinstance(rows, list):
        return []
    scored = [r for r in rows if isinstance(r, dict) and _row_value(r, domain) is not None]
    return sorted(scored, key=lambda r: _row_value(r, domain), reverse=True)


def _headline_metrics(result: dict, domain: str) -> dict[str, Any]:
    stats = result.get("summary_stats") or {}
    # spatial results nest headline under top_geo/top_poverty_geo
    nested = stats.get("top_geo") or stats.get("top_poverty_geo")
    merged = dict(stats)
    if isinstance(nested, dict):
        for k, v in nested.items():
            merged.setdefault(k, v)
    return merged


def _key_findings(result: dict, domain: str, units: list[dict]) -> list[str]:
    m = _headline_metrics(result, domain)
    findings: list[str] = []
    if domain == "poverty":
        if "headcount" in m:
            findings.append(f"Poverty headcount rate: {_pct(m.get('headcount'))} of the population falls below the poverty line.")
        if "poverty_gap" in m:
            findings.append(f"Poverty gap (average shortfall): {_pct(m.get('poverty_gap'))}.")
        if "gini" in m:
            findings.append(f"Inequality (Gini coefficient): {_num(m.get('gini'), 3)}.")
    elif domain == "agriculture":
        if m.get("crop_yield") is not None:
            findings.append(f"Average crop yield: {_num(m.get('crop_yield'))}.")
        for key, lbl in [("fertilizer_adoption_rate", "Fertilizer adoption"),
                         ("improved_seed_adoption_rate", "Improved-seed adoption"),
                         ("market_participation_rate", "Market participation")]:
            if m.get(key) is not None:
                findings.append(f"{lbl}: {_pct(m.get(key))}.")
    elif domain == "diversification":
        for key, lbl in [("crop_simpson_index", "Crop Simpson diversity"),
                         ("crop_shannon_index", "Crop Shannon diversity"),
                         ("income_diversification_simpson", "Income diversification (Simpson)")]:
            if m.get(key) is not None:
                findings.append(f"{lbl}: {_num(m.get(key), 3)}.")
    if units:
        vf = lambda r: _row_value(r, domain)  # noqa: E731
        hi, lo = units[0], units[-1]
        unit_word = "highest" if domain != "poverty" else "highest-poverty"
        val_fmt = _pct if domain == "poverty" else (lambda v: _num(v))
        findings.append(
            f"Geographic spread: {_row_label(hi)} shows the {unit_word} value "
            f"({val_fmt(vf(hi))}), while {_row_label(lo)} shows the lowest ({val_fmt(vf(lo))}), "
            f"across {len(units)} admin units."
        )
    return findings or ["The analysis completed but produced no headline metrics to summarise."]


def _recommendations(result: dict, domain: str, units: list[dict]) -> list[str]:
    m = _headline_metrics(result, domain)
    recs: list[str] = []
    top = _row_label(units[0]) if units else None
    if domain == "poverty":
        recs.append(
            f"Target social-protection and cash-transfer resources to the highest-poverty "
            f"admin units{f' (starting with {top})' if top else ''} to maximise impact per shilling."
        )
        if isinstance(m.get("gini"), (int, float)) and m["gini"] > 0.4:
            recs.append("With a Gini above 0.4, pair poverty programmes with progressive measures that address the underlying inequality.")
        recs.append("Track the poverty gap, not just the headcount, so programmes are judged on how far the poor are lifted, not only how many cross the line.")
    elif domain == "agriculture":
        recs.append(
            f"Prioritise extension services, input subsidies and irrigation in the lowest-yield "
            f"admin units to close the productivity gap."
        )
        if isinstance(m.get("fertilizer_adoption_rate"), (int, float)) and m["fertilizer_adoption_rate"] < 0.5:
            recs.append("Fertilizer adoption is below 50% — expand affordable-input and credit schemes to raise uptake.")
        recs.append("Strengthen market linkages where market participation is low so productivity gains translate into farm income.")
    elif domain == "diversification":
        recs.append("Support crop and income diversification in the least-diversified units to reduce household exposure to single-crop or single-source shocks.")
        recs.append("Combine diversification programmes with climate-risk and market-access support so new activities are viable, not just varied.")
    if units and len(units) >= 3:
        hotspots = ", ".join(_row_label(u) for u in units[:3])
        recs.append(f"Concentrate the first phase of intervention on the three priority units: {hotspots}.")
    return recs or ["Collect additional indicators to enable specific, targeted recommendations."]


def _default_questions(domain: str) -> list[str]:
    common = ["Which areas should be prioritised?", "What does this mean for policy?"]
    if domain == "poverty":
        return ["What is the overall poverty rate?", "Which area has the highest poverty?", "How unequal is welfare?"] + common
    if domain == "agriculture":
        return ["What is the average crop yield?", "Where is productivity lowest?", "How high is input adoption?"] + common
    return ["How diversified are livelihoods?", "Which area is least diversified?"] + common


def answer_question(question: str, result: dict, domain: str, units: list[dict]) -> str:
    q = (question or "").lower()
    m = _headline_metrics(result, domain)

    def top_unit() -> str:
        return _row_label(units[0]) if units else "the highest-ranked unit"

    def bottom_unit() -> str:
        return _row_label(units[-1]) if units else "the lowest-ranked unit"

    if any(w in q for w in ["poorest", "highest poverty", "most poverty", "worst off"]):
        return f"{top_unit()} has the highest poverty headcount in this analysis ({_pct(_row_value(units[0], 'poverty')) if units else '—'})."
    if any(w in q for w in ["richest", "lowest poverty", "least poverty", "best off"]):
        return f"{bottom_unit()} has the lowest poverty in this analysis."
    if any(w in q for w in ["inequality", "unequal", "gini", "equity"]):
        return f"The Gini coefficient is {_num(m.get('gini'), 3)} — higher values mean more unequal welfare."
    if any(w in q for w in ["overall", "average", "mean", "rate", "headcount"]):
        if domain == "poverty":
            return f"The overall poverty headcount rate is {_pct(m.get('headcount'))}, with a poverty gap of {_pct(m.get('poverty_gap'))}."
        if domain == "agriculture":
            return f"The average crop yield is {_num(m.get('crop_yield'))}."
        return f"The overall crop Simpson diversity index is {_num(m.get('crop_simpson_index'), 3)}."
    if any(w in q for w in ["yield", "productive", "productivity"]):
        return f"Average crop yield is {_num(m.get('crop_yield'))}; productivity is lowest in {bottom_unit()}."
    if any(w in q for w in ["adoption", "fertilizer", "seed", "input"]):
        return (f"Fertilizer adoption is {_pct(m.get('fertilizer_adoption_rate'))} and improved-seed adoption is "
                f"{_pct(m.get('improved_seed_adoption_rate'))}.")
    if any(w in q for w in ["diversif", "simpson", "shannon"]):
        return f"Crop diversification (Simpson) is {_num(m.get('crop_simpson_index'), 3)}; {bottom_unit()} is the least diversified."
    if any(w in q for w in ["how many", "number of", "units", "districts", "provinces", "regions"]):
        return f"The analysis covers {len(units)} geographic units." if units else "This analysis did not break results down by geographic unit."
    if any(w in q for w in ["priorit", "target", "where", "which area", "focus"]):
        if units:
            return "Priority areas (highest values first): " + ", ".join(_row_label(u) for u in units[:3]) + "."
        return "This analysis has no geographic breakdown; add a geography variable to prioritise areas."
    if any(w in q for w in ["policy", "mean", "implication", "recommend"]):
        recs = _recommendations(result, domain, units)
        return recs[0] if recs else "See the recommendations section."
    # fallback: reuse the analysis interpretation
    interp = result.get("interpretation_text")
    return interp or "The available aggregated results don't contain enough detail to answer that precisely."


def _to_markdown(brief: dict) -> str:
    lines = [f"# {brief['title']}", ""]
    lines.append(f"*Audience: {brief['audience']} · Generated: {brief['generated_at']}*")
    lines.append("")
    lines.append("## Executive summary")
    lines.append(brief["summary"])
    lines.append("")
    lines.append("## Key findings")
    for f in brief["key_findings"]:
        lines.append(f"- {f}")
    lines.append("")
    lines.append("## Recommendations")
    for i, r in enumerate(brief["recommendations"], 1):
        lines.append(f"{i}. {r}")
    lines.append("")
    if brief.get("qa"):
        lines.append("## Questions & answers")
        for qa in brief["qa"]:
            lines.append(f"**Q: {qa['question']}**")
            lines.append("")
            lines.append(qa["answer"])
            lines.append("")
    lines.append("---")
    lines.append("*Generated by the African Intelligence Cloud — LSMS & Microdata Analytics Engine. "
                 "Figures are aggregated; no respondent-level data is disclosed.*")
    return "\n".join(lines)


def generate_policy_brief(
    job_type: str,
    result: dict,
    *,
    title: str | None = None,
    audience: str = "policymakers",
    questions: list[str] | None = None,
) -> dict:
    domain = _DOMAIN_BY_JOBTYPE.get(str(job_type), "poverty")
    units = _ranked_units(result, domain)
    key_findings = _key_findings(result, domain, units)
    recommendations = _recommendations(result, domain, units)

    resolved_title = title or f"Policy Brief — {_DOMAIN_TITLE.get(domain, 'Analysis')} in Africa"
    summary_bits = [key_findings[0]] if key_findings else []
    if units:
        summary_bits.append(f"Results span {len(units)} admin units, with {_row_label(units[0])} standing out.")
    summary = " ".join(summary_bits) or (result.get("interpretation_text") or "See findings below.")

    qs = questions if questions else _default_questions(domain)
    qa = [{"question": q, "answer": answer_question(q, result, domain, units)} for q in qs]

    brief = {
        "title": resolved_title,
        "audience": audience,
        "domain": domain,
        "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC"),
        "summary": summary,
        "key_findings": key_findings,
        "recommendations": recommendations,
        "qa": qa,
        "sections": [
            {"heading": "Executive summary", "body": summary},
            {"heading": "Key findings", "body": "\n".join(f"- {f}" for f in key_findings)},
            {"heading": "Recommendations", "body": "\n".join(f"{i}. {r}" for i, r in enumerate(recommendations, 1))},
        ],
    }
    brief["markdown"] = _to_markdown(brief)
    return brief
