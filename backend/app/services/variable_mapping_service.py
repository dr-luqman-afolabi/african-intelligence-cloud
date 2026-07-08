"""Variable mapping engine — maps a survey's raw column names to canonical
StandardConcept values (household_id, welfare, gender, district, ...) so the
poverty/agriculture/diversification engines can run against any LSMS-family
survey without hardcoding each survey's own naming conventions.

Auto-detection is a heuristic keyword match against variable_name and
variable_label (both lower-cased). It never runs against raw data values —
only against the metadata already extracted at upload time — so it's safe to
run before any mapping has been confirmed by a user.
"""
from __future__ import annotations

from sqlalchemy.orm import Session

from app.models.microdata import StandardConcept, VariableMapping

# Ordered by specificity: earlier patterns win when a variable name could
# plausibly match more than one concept (e.g. "hhsize" must hit
# HOUSEHOLD_SIZE before the generic "hh" substring could pull it toward
# HOUSEHOLD_ID).
_CONCEPT_KEYWORDS: dict[StandardConcept, list[str]] = {
    StandardConcept.HOUSEHOLD_SIZE: ["hhsize", "household_size", "hh_size", "hsize", "famsize", "nmembers"],
    StandardConcept.HOUSEHOLD_ID: ["hhid", "household_id", "hh_id", "case_id", "hid"],
    StandardConcept.URBAN_RURAL: ["urban_rural", "urbrur", "rural_urban", "urban", "rural", "sector_ur"],
    StandardConcept.POVERTY_STATUS: ["poverty_status", "poor", "poverty_flag"],
    StandardConcept.WEIGHT: ["weight", "wgt", "hhweight", "pw", "wta_hh", "sample_weight"],
    StandardConcept.STRATA: ["strata", "stratum"],
    StandardConcept.CLUSTER: ["cluster", "psu", "ea_id", "enumeration_area"],
    StandardConcept.WELFARE: ["welfare", "expenditure", "totexp", "welfare_pc", "aggregate_consumption"],
    StandardConcept.CONSUMPTION: ["consumption", "consum", "cons_pc", "food_consumption"],
    StandardConcept.INCOME: ["income", "earnings", "wages", "revenue"],
    StandardConcept.GENDER: ["gender", "sex", "hh_head_sex", "male_female"],
    StandardConcept.AGE: ["age", "age_years", "age_yrs"],
    StandardConcept.EDUCATION: ["education", "educ", "school", "literacy", "grade_completed"],
    StandardConcept.DISTRICT: ["district"],
    StandardConcept.PROVINCE: ["province", "prov"],
    StandardConcept.REGION: ["region"],
    StandardConcept.SECTOR: ["sector"],
    StandardConcept.COUNTRY: ["country", "iso3", "country_code"],
    StandardConcept.LAND_AREA: ["land_area", "farm_size", "plot_area", "landsize", "acreage", "land_ha", "land_acres", "land"],
    StandardConcept.CROP_OUTPUT: ["crop_output", "harvest", "quantity_harvested", "output_kg", "yield"],
    StandardConcept.CROP_VALUE: ["crop_value", "value_harvest", "crop_sales", "value_production", "sales_value", "sales"],
    StandardConcept.LIVESTOCK: ["livestock", "cattle", "tlu", "animal"],
    StandardConcept.FERTILIZER: ["fertilizer", "fert_use", "inorganic_fert"],
    StandardConcept.IMPROVED_SEED: ["improved_seed", "hybrid_seed", "certified_seed"],
    StandardConcept.IRRIGATION: ["irrigation", "irrigated"],
    StandardConcept.EXTENSION: ["extension", "ext_visit", "advisory_service"],
}

# Concepts checked in this order so the more specific patterns above are
# tried before generic ones (e.g. HOUSEHOLD_SIZE before HOUSEHOLD_ID).
_DETECTION_ORDER = list(_CONCEPT_KEYWORDS.keys())


def _score(text: str, keyword: str) -> int:
    """Confidence score (0-100) for one keyword against one text field."""
    if text == keyword:
        return 100
    if text.startswith(keyword) or text.endswith(keyword):
        return 85
    if keyword in text:
        return 70
    return 0


def suggest_mappings(variables: list[dict]) -> list[dict]:
    """Given extracted variable metadata (variable_name, variable_label),
    return the best-guess StandardConcept mapping per candidate variable.

    Returns a list of {standard_concept, raw_variable_name, confidence}
    sorted by confidence descending, at most one suggestion per concept
    (the highest-confidence match among all variables for that concept) and
    at most one concept suggested per raw variable (its best-scoring concept).
    """
    best_per_concept: dict[StandardConcept, tuple[str, int]] = {}
    best_per_variable: dict[str, tuple[StandardConcept, int]] = {}

    for var in variables:
        name = (var.get("variable_name") or "").strip().lower()
        label = (var.get("variable_label") or "").strip().lower()
        if not name:
            continue

        for concept in _DETECTION_ORDER:
            keywords = _CONCEPT_KEYWORDS[concept]
            best_score = 0
            for kw in keywords:
                best_score = max(best_score, _score(name, kw))
                if label:
                    # Label matches are corroborating evidence, not primary —
                    # cap below a pure name match so "age" in a free-text
                    # label doesn't outrank an exact "age" column name.
                    best_score = max(best_score, min(_score(label, kw), 60))
            if best_score == 0:
                continue

            current_best_var = best_per_variable.get(var["variable_name"])
            if current_best_var is None or best_score > current_best_var[1]:
                best_per_variable[var["variable_name"]] = (concept, best_score)

            current_best_concept = best_per_concept.get(concept)
            if current_best_concept is None or best_score > current_best_concept[1]:
                best_per_concept[concept] = (var["variable_name"], best_score)

    # Reconcile: only keep a concept<->variable pair if each is the other's
    # best match, avoiding one strong variable "stealing" a concept from a
    # sibling variable that's actually a better fit for something else.
    suggestions = []
    for concept, (raw_name, score) in best_per_concept.items():
        if best_per_variable.get(raw_name, (None, 0))[0] == concept:
            suggestions.append({
                "standard_concept": concept.value,
                "raw_variable_name": raw_name,
                "confidence": score,
            })

    return sorted(suggestions, key=lambda s: s["confidence"], reverse=True)


def save_mappings(
    db: Session,
    dataset_id,
    mappings: list[dict],
    user_id=None,
    auto_detected: bool = False,
) -> list[VariableMapping]:
    """Upsert mappings for a dataset — one row per standard_concept.
    `mappings` is a list of {standard_concept, raw_variable_name, confidence?}."""
    existing = {
        m.standard_concept.value: m
        for m in db.query(VariableMapping).filter(VariableMapping.dataset_id == dataset_id).all()
    }

    saved = []
    for m in mappings:
        concept = StandardConcept(m["standard_concept"])
        row = existing.get(concept.value)
        if row:
            row.raw_variable_name = m["raw_variable_name"]
            row.confidence = m.get("confidence")
            row.auto_detected = auto_detected
            row.created_by = user_id if not auto_detected else row.created_by
        else:
            row = VariableMapping(
                dataset_id=dataset_id,
                standard_concept=concept,
                raw_variable_name=m["raw_variable_name"],
                confidence=m.get("confidence"),
                auto_detected=auto_detected,
                created_by=user_id,
            )
            db.add(row)
        saved.append(row)

    db.commit()
    for row in saved:
        db.refresh(row)
    return saved


def get_mappings_dict(db: Session, dataset_id) -> dict[str, str]:
    """Return {standard_concept: raw_variable_name} for a dataset — the shape
    the analysis engines consume to resolve a concept to an actual column."""
    rows = db.query(VariableMapping).filter(VariableMapping.dataset_id == dataset_id).all()
    return {row.standard_concept.value: row.raw_variable_name for row in rows}
