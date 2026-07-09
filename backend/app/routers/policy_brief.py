"""AI Policy Brief endpoint — generate a download-ready policy brief (with a
data-grounded Q&A section) directly from a completed analysis result."""
from __future__ import annotations

import logging
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.microdata import (
    MicrodataAnalysisJob,
    MicrodataAnalysisResult,
    MicrodataDataset,
)
from app.schemas.microdata import PolicyBriefRequest, PolicyBriefResponse
from app.services.auth_service import get_current_user
from app.services.policy_brief_service import generate_policy_brief

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/microdata", tags=["AI Policy Brief"])
security = HTTPBearer()


def _get_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db),
):
    return get_current_user(db, credentials.credentials)


@router.post("/policy-brief", response_model=PolicyBriefResponse)
def create_policy_brief(
    payload: PolicyBriefRequest,
    db: Session = Depends(get_db),
    current_user=Depends(_get_user),
):
    job = db.query(MicrodataAnalysisJob).filter(MicrodataAnalysisJob.id == payload.job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Analysis job not found")

    dataset = db.query(MicrodataDataset).filter(MicrodataDataset.id == job.dataset_id).first()
    if not dataset or dataset.uploaded_by != current_user.id:
        raise HTTPException(status_code=403, detail="You do not have access to this analysis")

    result = (
        db.query(MicrodataAnalysisResult)
        .filter(MicrodataAnalysisResult.job_id == job.id)
        .order_by(MicrodataAnalysisResult.created_at.desc())
        .first()
    )
    if not result:
        raise HTTPException(status_code=404, detail="No result available for this job yet")

    result_dict = {
        "summary_stats": result.summary_stats,
        "tables": result.tables,
        "charts": result.charts,
        "geojson": result.geojson,
        "interpretation_text": result.interpretation_text,
    }
    brief = generate_policy_brief(
        job.job_type.value,
        result_dict,
        title=payload.title,
        audience=payload.audience or "policymakers",
        questions=payload.questions,
    )
    brief["job_id"] = job.id
    return brief
