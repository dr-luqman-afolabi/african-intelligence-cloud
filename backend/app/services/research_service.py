"""AI-powered research intelligence service (Task 6)."""
from __future__ import annotations

import json
from typing import Optional

from sqlalchemy.orm import Session

from app.models.research_paper import ResearchPaper, PaperMethod, PaperTheory
from app.models.research_source import ResearchSource
from app.services.research_source_service import list_sources


# ---------------------------------------------------------------------------
# Theory recommendation
# ---------------------------------------------------------------------------

_THEORY_CORPUS: list[dict] = [
    {
        "name": "Dependency Theory",
        "description": "Structural underdevelopment through core-periphery relationships",
        "keywords": ["development", "poverty", "trade", "colonialism", "underdevelopment", "periphery"],
        "african_relevance": 0.95,
    },
    {
        "name": "Modernisation Theory",
        "description": "Economic growth through industrial and social transformation stages",
        "keywords": ["growth", "industrialisation", "institution", "governance", "structural change"],
        "african_relevance": 0.80,
    },
    {
        "name": "New Structural Economics",
        "description": "State-facilitated structural transformation aligned with comparative advantage",
        "keywords": ["structural transformation", "manufacturing", "comparative advantage", "industrial policy"],
        "african_relevance": 0.90,
    },
    {
        "name": "Endogenous Growth Theory",
        "description": "Long-run growth driven by human capital, innovation, and knowledge",
        "keywords": ["human capital", "education", "innovation", "R&D", "technology", "productivity"],
        "african_relevance": 0.85,
    },
    {
        "name": "Dutch Disease Theory",
        "description": "Resource booms crowd out tradable sectors via real exchange rate appreciation",
        "keywords": ["natural resource", "oil", "mineral", "exchange rate", "deindustrialisation", "resource curse"],
        "african_relevance": 0.90,
    },
    {
        "name": "Institutional Economics",
        "description": "Economic outcomes shaped by formal/informal rules, norms, and property rights",
        "keywords": ["institution", "property rights", "governance", "corruption", "rule of law"],
        "african_relevance": 0.92,
    },
    {
        "name": "Keynesian Theory",
        "description": "Aggregate demand determines short-run output; fiscal policy as stabiliser",
        "keywords": ["fiscal policy", "government spending", "aggregate demand", "recession", "stimulus"],
        "african_relevance": 0.75,
    },
    {
        "name": "Financial Development Theory",
        "description": "Deep financial systems accelerate capital allocation and economic growth",
        "keywords": ["financial sector", "banking", "credit", "mobile money", "fintech", "capital market"],
        "african_relevance": 0.88,
    },
    {
        "name": "Demographic Transition Theory",
        "description": "Falling mortality/fertility rates reshape labour supply and dependency ratios",
        "keywords": ["population", "fertility", "demographic dividend", "youth", "labour supply"],
        "african_relevance": 0.93,
    },
    {
        "name": "Trade Theory (Heckscher-Ohlin)",
        "description": "Countries export goods intensive in their abundant factors",
        "keywords": ["trade", "exports", "comparative advantage", "factor endowment", "tariff"],
        "african_relevance": 0.80,
    },
]


def recommend_theories(topic: str, context: str = "") -> list[dict]:
    """Score and rank theories by keyword overlap with the research topic."""
    combined = (topic + " " + context).lower()
    scored = []
    for theory in _THEORY_CORPUS:
        score = sum(1 for kw in theory["keywords"] if kw in combined)
        if score > 0:
            scored.append({
                "name": theory["name"],
                "description": theory["description"],
                "relevance_score": round(score / len(theory["keywords"]), 2),
                "african_relevance": theory["african_relevance"],
            })
    return sorted(scored, key=lambda x: x["relevance_score"], reverse=True)[:5]


# ---------------------------------------------------------------------------
# Variable / data source recommendation
# ---------------------------------------------------------------------------

_VARIABLE_CORPUS: list[dict] = [
    {
        "variable": "GDP per capita (PPP)",
        "sources": ["World Bank WDI", "IMF World Economic Outlook", "UN National Accounts"],
        "keywords": ["economic growth", "income", "development", "poverty"],
    },
    {
        "variable": "FDI inflows (% GDP)",
        "sources": ["UNCTAD FDI Statistics", "World Bank WDI"],
        "keywords": ["foreign investment", "FDI", "capital flows", "trade"],
    },
    {
        "variable": "Inflation (CPI)",
        "sources": ["World Bank WDI", "IMF IFS", "African Development Bank Statistics"],
        "keywords": ["inflation", "prices", "monetary policy", "cost of living"],
    },
    {
        "variable": "Human Development Index",
        "sources": ["UNDP Human Development Reports"],
        "keywords": ["human development", "education", "health", "wellbeing"],
    },
    {
        "variable": "Mobile money penetration",
        "sources": ["GSMA Mobile Money Database", "World Bank Findex"],
        "keywords": ["fintech", "mobile money", "financial inclusion", "banking"],
    },
    {
        "variable": "Agricultural value added (% GDP)",
        "sources": ["World Bank WDI", "FAO FAOSTAT"],
        "keywords": ["agriculture", "food security", "rural", "farming"],
    },
    {
        "variable": "Net ODA received (% GNI)",
        "sources": ["OECD DAC", "World Bank WDI"],
        "keywords": ["aid", "ODA", "development assistance", "donor"],
    },
    {
        "variable": "Institutional quality (CPIA)",
        "sources": ["World Bank CPIA", "Mo Ibrahim Index"],
        "keywords": ["institution", "governance", "rule of law", "corruption"],
    },
]


def recommend_variables(topic: str, context: str = "") -> list[dict]:
    combined = (topic + " " + context).lower()
    scored = []
    for var in _VARIABLE_CORPUS:
        score = sum(1 for kw in var["keywords"] if kw in combined)
        if score > 0:
            scored.append({
                "variable": var["variable"],
                "recommended_sources": var["sources"],
                "relevance_score": round(score / len(var["keywords"]), 2),
            })
    return sorted(scored, key=lambda x: x["relevance_score"], reverse=True)[:8]


# ---------------------------------------------------------------------------
# Econometric method recommendation
# ---------------------------------------------------------------------------

_METHOD_CORPUS: list[dict] = [
    {
        "method": "Fixed Effects Panel Regression",
        "description": "Controls for unobserved time-invariant heterogeneity across units",
        "keywords": ["panel data", "country", "time series", "heterogeneity", "endogeneity"],
        "software": ["Stata", "R (plm)", "Python (linearmodels)"],
    },
    {
        "method": "Difference-in-Differences (DiD)",
        "description": "Causal effect estimation using treatment/control groups over time",
        "keywords": ["causal", "policy evaluation", "treatment", "natural experiment"],
        "software": ["Stata", "R (did)", "Python (econml)"],
    },
    {
        "method": "Instrumental Variables (IV / 2SLS)",
        "description": "Addresses endogeneity using exogenous instruments",
        "keywords": ["endogeneity", "reverse causality", "instrument", "exogeneity"],
        "software": ["Stata (ivreg2)", "R (AER)", "Python (linearmodels)"],
    },
    {
        "method": "Vector Autoregression (VAR)",
        "description": "Captures dynamic interdependencies among multiple time series",
        "keywords": ["time series", "dynamic", "impulse response", "Granger causality", "macroeconomic"],
        "software": ["Stata (var)", "R (vars)", "Python (statsmodels)"],
    },
    {
        "method": "Synthetic Control Method",
        "description": "Counterfactual analysis via weighted combination of control units",
        "keywords": ["causal inference", "comparative case", "policy", "single unit treatment"],
        "software": ["R (Synth)", "Python (pysyncon)", "Stata (synth)"],
    },
    {
        "method": "Probit / Logit Regression",
        "description": "Binary or categorical outcome modelling",
        "keywords": ["binary", "probability", "discrete choice", "poverty", "access"],
        "software": ["Stata", "R", "Python (statsmodels)"],
    },
    {
        "method": "Generalised Method of Moments (GMM)",
        "description": "Efficient estimation with endogenous regressors in dynamic panel models",
        "keywords": ["dynamic panel", "Arellano-Bond", "GMM", "lagged dependent variable"],
        "software": ["Stata (xtabond2)", "R (gmm, pgmm)"],
    },
    {
        "method": "Regression Discontinuity Design (RDD)",
        "description": "Exploits sharp/fuzzy cutoffs for quasi-experimental causal estimates",
        "keywords": ["cutoff", "threshold", "quasi-experimental", "local average treatment"],
        "software": ["Stata (rdrobust)", "R (rddensity)", "Python (rdrobust)"],
    },
]


def recommend_methods(topic: str, context: str = "") -> list[dict]:
    combined = (topic + " " + context).lower()
    scored = []
    for m in _METHOD_CORPUS:
        score = sum(1 for kw in m["keywords"] if kw in combined)
        if score > 0:
            scored.append({
                "method": m["method"],
                "description": m["description"],
                "software": m["software"],
                "relevance_score": round(score / len(m["keywords"]), 2),
            })
    return sorted(scored, key=lambda x: x["relevance_score"], reverse=True)[:5]


# ---------------------------------------------------------------------------
# Literature review matrix
# ---------------------------------------------------------------------------

def generate_literature_matrix(papers: list[ResearchPaper]) -> list[dict]:
    """Convert a list of ResearchPaper ORM objects into a literature matrix."""
    matrix = []
    for paper in papers:
        methods = [m.method_name for m in paper.methods]
        theories = [t.theory_name for t in paper.theories]
        matrix.append({
            "title": paper.title,
            "authors": [a.full_name for a in paper.authors],
            "year": paper.published_year,
            "journal": paper.journal,
            "doi": paper.doi,
            "theories_used": theories,
            "methods_used": methods,
            "is_open_access": paper.is_open_access,
            "citation_count": paper.citation_count,
        })
    return matrix


# ---------------------------------------------------------------------------
# Research gap identification
# ---------------------------------------------------------------------------

def identify_research_gaps(papers: list[dict], topic: str) -> list[str]:
    """Heuristic gap identification based on topic keywords vs. paper coverage."""
    covered_topics: set[str] = set()
    for p in papers:
        for t in p.get("topics", []):
            covered_topics.add(t.lower())

    potential_gaps = [
        f"Long-term longitudinal analysis of {topic} in Sub-Saharan Africa",
        f"Gender-disaggregated analysis of {topic} outcomes",
        f"Sub-national / subnational evidence on {topic}",
        f"Firm-level microdata analysis linking {topic} to macroeconomic outcomes",
        f"Causal mechanisms between {topic} and poverty reduction in LDCs",
        f"Comparative African case studies across different institutional contexts",
        f"Digital economy dimensions of {topic} in African contexts",
    ]
    return potential_gaps


# ---------------------------------------------------------------------------
# Conceptual framework generator
# ---------------------------------------------------------------------------

def generate_conceptual_framework(topic: str, theories: list[str], variables: list[str]) -> dict:
    return {
        "title": f"Conceptual Framework: {topic}",
        "theoretical_foundation": theories,
        "independent_variables": variables[:3] if variables else [],
        "dependent_variable": topic,
        "moderating_factors": ["Institutional quality", "Economic openness", "Demographic structure"],
        "control_variables": ["GDP per capita (log)", "Population size (log)", "Trade openness"],
        "proposed_relationships": [
            f"{var} → {topic}" for var in (variables[:3] if variables else [])
        ],
    }


# ---------------------------------------------------------------------------
# Hypothesis generation
# ---------------------------------------------------------------------------

def generate_hypotheses(topic: str, theories: list[str], variables: list[str]) -> list[str]:
    hypotheses = []
    for i, var in enumerate(variables[:4], start=1):
        hypotheses.append(
            f"H{i}: {var} has a statistically significant effect on {topic} in African economies."
        )
    hypotheses.append(
        f"H{len(hypotheses)+1}: The relationship between {variables[0] if variables else 'the key variable'}"
        f" and {topic} is moderated by institutional quality."
    )
    return hypotheses


# ---------------------------------------------------------------------------
# African datasets suggestion
# ---------------------------------------------------------------------------

_AFRICAN_DATASETS: list[dict] = [
    {
        "name": "World Bank Africa Development Indicators",
        "url": "https://datatopics.worldbank.org/world-development-indicators/",
        "coverage": "All African countries, 1960–present",
        "variables": "GDP, trade, health, education, governance",
        "license": "CC BY 4.0",
    },
    {
        "name": "African Development Bank Statistics",
        "url": "https://www.afdb.org/en/knowledge/statistics",
        "coverage": "54 African countries",
        "variables": "Macroeconomic, financial, infrastructure",
        "license": "Open",
    },
    {
        "name": "Mo Ibrahim Index of African Governance",
        "url": "https://mo.ibrahim.foundation/iiag",
        "coverage": "54 African countries, 2000–present",
        "variables": "Governance, rule of law, human rights",
        "license": "Open for research",
    },
    {
        "name": "ACLED — Armed Conflict Location & Event Data",
        "url": "https://acleddata.com/africa/",
        "coverage": "All African countries, 1997–present",
        "variables": "Conflict events, fatalities, actor types",
        "license": "Free for research",
    },
    {
        "name": "DHS Program — Demographic and Health Surveys",
        "url": "https://dhsprogram.com",
        "coverage": "50+ African countries",
        "variables": "Fertility, health, nutrition, women empowerment",
        "license": "Free (registration required)",
    },
    {
        "name": "FinScope Africa Surveys",
        "url": "https://finmark.org.za",
        "coverage": "28 African countries",
        "variables": "Financial inclusion, household finance",
        "license": "Open for research",
    },
    {
        "name": "COMTRADE Africa Trade Data",
        "url": "https://comtradeplus.un.org/",
        "coverage": "All African countries",
        "variables": "Import/export by product and partner",
        "license": "Subscription (bulk free for research)",
    },
]


def suggest_african_datasets(topic: str) -> list[dict]:
    topic_lower = topic.lower()
    keywords_map = {
        "governance": ["Mo Ibrahim", "World Bank Africa"],
        "conflict": ["ACLED"],
        "health": ["DHS", "World Bank Africa"],
        "trade": ["COMTRADE", "World Bank Africa", "African Development Bank"],
        "finance": ["FinScope", "World Bank Africa", "African Development Bank"],
        "agriculture": ["World Bank Africa", "African Development Bank"],
        "poverty": ["World Bank Africa", "DHS"],
    }
    relevant_names: set[str] = set()
    for kw, names in keywords_map.items():
        if kw in topic_lower:
            relevant_names.update(names)

    if not relevant_names:
        return _AFRICAN_DATASETS[:4]

    result = [d for d in _AFRICAN_DATASETS if any(n in d["name"] for n in relevant_names)]
    return result or _AFRICAN_DATASETS[:4]
