from __future__ import annotations

import logging
from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy.orm import Session

from app.models.quality_score import QualityScore

logger = logging.getLogger(__name__)

_CURRENT_YEAR = datetime.now(timezone.utc).year
_TARGET_COUNTRIES = 54  # UN-recognised African states


def compute_quality(
    db: Session,
    sync_job_id: UUID,
    source_id: str,
    records: list[dict],
) -> QualityScore:
    """Compute and persist a QualityScore for one sync run."""

    total = len(records)
    if total == 0:
        score = QualityScore(
            sync_job_id=sync_job_id,
            source_id=source_id,
            overall_score=0.0,
            total_records=0,
        )
        db.add(score)
        db.commit()
        return score

    # Completeness: non-null values
    null_count = sum(1 for r in records if r.get("value") is None)
    completeness = round((1 - null_count / total) * 100, 2)

    # Timeliness: most-recent year in data vs current year
    years = [r["year"] for r in records if isinstance(r.get("year"), int)]
    if years:
        most_recent = max(years)
        lag = max(0, _CURRENT_YEAR - most_recent)
        timeliness = max(0.0, round((1 - lag / 10) * 100, 2))
    else:
        timeliness = 0.0

    # Coverage: unique countries vs 54 African states
    countries = {r.get("country_iso3") for r in records if r.get("country_iso3")}
    coverage = round(min(len(countries) / _TARGET_COUNTRIES, 1.0) * 100, 2)

    # Consistency: values that are numeric (non-NaN, finite)
    import math
    numeric_values = [r["value"] for r in records if isinstance(r.get("value"), (int, float))]
    bad_values = sum(1 for v in numeric_values if not math.isfinite(v))
    outlier_count = bad_values
    consistency = round((1 - bad_values / max(len(numeric_values), 1)) * 100, 2)

    overall = round((completeness + timeliness + coverage + consistency) / 4, 2)

    score = QualityScore(
        sync_job_id=sync_job_id,
        source_id=source_id,
        overall_score=overall,
        completeness_score=completeness,
        timeliness_score=timeliness,
        coverage_score=coverage,
        consistency_score=consistency,
        total_records=total,
        null_count=null_count,
        outlier_count=outlier_count,
    )
    db.add(score)
    db.commit()

    logger.info(
        "Quality score for %s: overall=%.1f completeness=%.1f timeliness=%.1f coverage=%.1f",
        source_id, overall, completeness, timeliness, coverage,
    )
    return score
