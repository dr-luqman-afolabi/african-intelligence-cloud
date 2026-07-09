"""Interactive Spatial Explorer — session CRUD + run endpoints.

A session bundles a dataset + admin boundaries + an active analytical layer
(poverty / agriculture / diversification) + row filters + variable selections,
all persisted so an exploration can be saved and replayed. Running a session
recomputes an aggregated, choropleth-ready result (Moran's I / LISA included)
via the shared spatial analysis services.
"""
from __future__ import annotations

import logging
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.microdata import (
    ExplorerLayer,
    MicrodataAnalysisJob,
    MicrodataAnalysisResult,
    MicrodataDataset,
    MicrodataExplorerSession,
)
from app.schemas.microdata import (
    AnalysisResultResponse,
    ExplorerRunRequest,
    ExplorerSessionCreate,
    ExplorerSessionResponse,
    ExplorerSessionUpdate,
)
from app.services.auth_service import get_current_user
from app.services.explorer_session_service import coerce_layer, run_session_layer

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/microdata/sessions", tags=["Microdata Explorer"])
security = HTTPBearer()


def _get_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db),
):
    return get_current_user(db, credentials.credentials)


def _get_owned_session(db: Session, session_id: UUID, current_user) -> MicrodataExplorerSession:
    session = (
        db.query(MicrodataExplorerSession)
        .filter(MicrodataExplorerSession.id == session_id)
        .first()
    )
    if not session:
        raise HTTPException(status_code=404, detail="Explorer session not found")
    if session.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="You do not have access to this session")
    return session


def _validate_dataset(db: Session, dataset_id, current_user) -> None:
    if dataset_id is None:
        return
    dataset = db.query(MicrodataDataset).filter(MicrodataDataset.id == dataset_id).first()
    if not dataset:
        raise HTTPException(status_code=404, detail="Dataset not found")
    if dataset.uploaded_by != current_user.id:
        raise HTTPException(status_code=403, detail="You do not have access to this dataset")


@router.post("", response_model=ExplorerSessionResponse, status_code=201)
def create_session(
    payload: ExplorerSessionCreate,
    db: Session = Depends(get_db),
    current_user=Depends(_get_user),
):
    _validate_dataset(db, payload.dataset_id, current_user)
    session = MicrodataExplorerSession(
        name=payload.name or "Untitled exploration",
        owner_id=current_user.id,
        dataset_id=payload.dataset_id,
        country_iso3=payload.country_iso3,
        admin_level=payload.admin_level,
        active_layer=coerce_layer(payload.active_layer or "poverty"),
        state=payload.state or {},
    )
    db.add(session)
    db.commit()
    db.refresh(session)
    return session


@router.get("", response_model=list[ExplorerSessionResponse])
def list_sessions(
    db: Session = Depends(get_db),
    current_user=Depends(_get_user),
):
    return (
        db.query(MicrodataExplorerSession)
        .filter(MicrodataExplorerSession.owner_id == current_user.id)
        .order_by(MicrodataExplorerSession.updated_at.desc())
        .all()
    )


@router.get("/{session_id}", response_model=ExplorerSessionResponse)
def get_session(
    session_id: UUID,
    db: Session = Depends(get_db),
    current_user=Depends(_get_user),
):
    return _get_owned_session(db, session_id, current_user)


@router.patch("/{session_id}", response_model=ExplorerSessionResponse)
def update_session(
    session_id: UUID,
    payload: ExplorerSessionUpdate,
    db: Session = Depends(get_db),
    current_user=Depends(_get_user),
):
    session = _get_owned_session(db, session_id, current_user)
    data = payload.model_dump(exclude_unset=True)
    if "dataset_id" in data:
        _validate_dataset(db, data["dataset_id"], current_user)
        session.dataset_id = data["dataset_id"]
    if "name" in data and data["name"] is not None:
        session.name = data["name"]
    if "country_iso3" in data:
        session.country_iso3 = data["country_iso3"]
    if "admin_level" in data:
        session.admin_level = data["admin_level"]
    if "active_layer" in data and data["active_layer"] is not None:
        session.active_layer = coerce_layer(data["active_layer"])
    if "state" in data and data["state"] is not None:
        # merge, so partial saves (e.g. just map_view) don't wipe other keys
        merged = dict(session.state or {})
        merged.update(data["state"])
        session.state = merged
    db.add(session)
    db.commit()
    db.refresh(session)
    return session


@router.delete("/{session_id}", status_code=204)
def delete_session(
    session_id: UUID,
    db: Session = Depends(get_db),
    current_user=Depends(_get_user),
):
    session = _get_owned_session(db, session_id, current_user)
    db.delete(session)
    db.commit()
    return None


@router.post("/{session_id}/run", response_model=AnalysisResultResponse)
def run_session(
    session_id: UUID,
    payload: ExplorerRunRequest | None = None,
    db: Session = Depends(get_db),
    current_user=Depends(_get_user),
):
    """Recompute the session's active layer over its filtered dataset and
    return an aggregated, choropleth-ready result. Optional overrides in the
    request body are persisted to the session first (so replay stays in sync)."""
    session = _get_owned_session(db, session_id, current_user)
    if payload:
        if payload.active_layer is not None:
            session.active_layer = coerce_layer(payload.active_layer)
        if payload.state is not None:
            merged = dict(session.state or {})
            merged.update(payload.state)
            session.state = merged
        db.add(session)
        db.commit()
        db.refresh(session)
    return run_session_layer(db, session, current_user)


@router.get("/{session_id}/result", response_model=AnalysisResultResponse)
def get_session_result(
    session_id: UUID,
    db: Session = Depends(get_db),
    current_user=Depends(_get_user),
):
    """Fetch the most recent analysis result for this session (for replay)."""
    session = _get_owned_session(db, session_id, current_user)
    if not session.last_result_job_id:
        raise HTTPException(status_code=404, detail="This session has not been run yet")
    job = (
        db.query(MicrodataAnalysisJob)
        .filter(MicrodataAnalysisJob.id == session.last_result_job_id)
        .first()
    )
    if not job:
        raise HTTPException(status_code=404, detail="Result job not found")
    result = (
        db.query(MicrodataAnalysisResult)
        .filter(MicrodataAnalysisResult.job_id == job.id)
        .order_by(MicrodataAnalysisResult.created_at.desc())
        .first()
    )
    return {
        "job_id": job.id,
        "status": job.status,
        "job_type": job.job_type,
        "summary_stats": result.summary_stats if result else None,
        "tables": result.tables if result else None,
        "charts": result.charts if result else None,
        "geojson": result.geojson if result else None,
        "interpretation_text": result.interpretation_text if result else None,
        "error_message": job.error_message,
    }
