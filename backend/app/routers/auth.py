from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.user import User, UserRole
from app.schemas.auth import (
    RegisterRequest,
    LoginRequest,
    RoleUpdateRequest,
    TokenResponse,
    UserProfile,
)
from app.services import auth_service

router = APIRouter(prefix="/auth", tags=["Authentication"])
_bearer = HTTPBearer()


@router.post("/register", response_model=UserProfile, status_code=201)
def register(payload: RegisterRequest, db: Session = Depends(get_db)):
    user = auth_service.register_user(
        db, payload.email, payload.full_name, payload.password
    )
    return user


@router.post("/login", response_model=TokenResponse)
def login(payload: LoginRequest, db: Session = Depends(get_db)):
    user = auth_service.authenticate_user(db, payload.email, payload.password)
    token = auth_service.create_access_token({"sub": str(user.id)})
    return {"access_token": token}


@router.get("/profile", response_model=UserProfile)
def profile(
    credentials: HTTPAuthorizationCredentials = Depends(_bearer),
    db: Session = Depends(get_db),
):
    user = auth_service.get_current_user(db, credentials.credentials)
    return user


def require_admin(
    credentials: HTTPAuthorizationCredentials = Depends(_bearer),
    db: Session = Depends(get_db),
) -> User:
    """Reusable dependency: only SUPER_ADMIN or ORG_ADMIN may proceed."""
    user = auth_service.get_current_user(db, credentials.credentials)
    if user.role not in (UserRole.SUPER_ADMIN, UserRole.ORG_ADMIN):
        raise HTTPException(status_code=403, detail="Admin privileges required")
    return user


@router.get("/pending", response_model=list[UserProfile])
def pending_users(
    admin: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    return auth_service.list_pending_users(db)


@router.post("/approve/{user_id}", response_model=UserProfile)
def approve_pending_user(
    user_id: UUID,
    admin: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    return auth_service.approve_user(db, user_id)


@router.get("/users", response_model=list[UserProfile])
def all_users(
    admin: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    return auth_service.list_all_users(db)


@router.delete("/reject/{user_id}", status_code=204)
def reject_pending_user(
    user_id: UUID,
    admin: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    auth_service.reject_user(db, admin, user_id)


@router.post("/users/{user_id}/activate", response_model=UserProfile)
def activate_user(
    user_id: UUID,
    admin: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    return auth_service.set_user_active(db, admin, user_id, True)


@router.post("/users/{user_id}/deactivate", response_model=UserProfile)
def deactivate_user(
    user_id: UUID,
    admin: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    return auth_service.set_user_active(db, admin, user_id, False)


@router.patch("/users/{user_id}/role", response_model=UserProfile)
def update_user_role(
    user_id: UUID,
    payload: RoleUpdateRequest,
    admin: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    return auth_service.set_user_role(db, admin, user_id, payload.role)
