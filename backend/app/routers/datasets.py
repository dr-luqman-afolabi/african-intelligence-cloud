import logging
from uuid import UUID

from fastapi import APIRouter, BackgroundTasks, Depends, File, Form, HTTPException, Request, UploadFile
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.dataset import DatasetStatus
from app.schemas.dataset import (
    DatasetDetailResponse,
    DatasetListResponse,
    DatasetUploadResponse,
    ProfileTriggerResponse,
)
from app.services.auth_service import get_current_user
from app.services.dataset_service import (
    _run_profiling_background,
    delete_dataset,
    get_dataset_by_id,
    get_datasets_for_user,
    trigger_profiling,
    upload_dataset,
)

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/datasets", tags=["datasets"])
security = HTTPBearer()


def _get_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db),
):
    return get_current_user(credentials.credentials, db)


def _client_ip(request: Request) -> str:
    forwarded = request.headers.get("x-forwarded-for")
    return forwarded.split(",")[0].strip() if forwarded else (request.client.host if request.client else "")


@router.post("/upload", response_model=DatasetUploadResponse, status_code=201)
async def upload_dataset_endpoint(
    request: Request,
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    name: str = Form(...),
    description: str | None = Form(None),
    privacy: str = Form("private"),
    tags: str | None = Form(None),
    db: Session = Depends(get_db),
    current_user=Depends(_get_user),
):
    """Upload a dataset file (CSV, XLSX, XLS, JSON, Parquet)."""
    if privacy not in ("private", "organization", "public"):
        raise HTTPException(status_code=422, detail="privacy must be private, organization, or public")

    parsed_tags: list[str] = []
    if tags:
        parsed_tags = [t.strip() for t in tags.split(",") if t.strip()]

    try:
        dataset = await upload_dataset(
            db=db,
            file=file,
            name=name,
            description=description,
            privacy=privacy,
            tags=parsed_tags,
            current_user=current_user,
            client_ip=_client_ip(request),
            user_agent=request.headers.get("user-agent", ""),
        )
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc))

    return dataset


@router.get("", response_model=DatasetListResponse)
def list_datasets(
    page: int = 1,
    page_size: int = 20,
    db: Session = Depends(get_db),
    current_user=Depends(_get_user),
):
    """List datasets visible to the current user."""
    if page < 1:
        page = 1
    if page_size < 1 or page_size > 100:
        page_size = 20

    items, total = get_datasets_for_user(db, current_user, page=page, page_size=page_size)
    return DatasetListResponse(items=items, total=total, page=page, page_size=page_size)


@router.get("/{dataset_id}", response_model=DatasetDetailResponse)
def get_dataset(
    dataset_id: UUID,
    db: Session = Depends(get_db),
    current_user=Depends(_get_user),
):
    """Get full dataset detail including profile and column metadata."""
    return get_dataset_by_id(db, dataset_id, current_user)


@router.post("/{dataset_id}/profile", response_model=ProfileTriggerResponse)
def profile_dataset(
    dataset_id: UUID,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user=Depends(_get_user),
):
    """Trigger background profiling for a dataset."""
    dataset = trigger_profiling(db, dataset_id, current_user)
    background_tasks.add_task(_run_profiling_background, str(dataset_id))
    return ProfileTriggerResponse(
        message="Profiling started",
        dataset_id=dataset_id,
        status=DatasetStatus.PROFILING,
    )


@router.delete("/{dataset_id}", status_code=204)
def delete_dataset_endpoint(
    request: Request,
    dataset_id: UUID,
    db: Session = Depends(get_db),
    current_user=Depends(_get_user),
):
    """Delete a dataset and its stored file. Only the uploader may delete."""
    delete_dataset(
        db,
        dataset_id,
        current_user,
        ip=_client_ip(request),
        user_agent=request.headers.get("user-agent", ""),
    )
