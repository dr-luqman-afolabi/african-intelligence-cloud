from datetime import datetime, timedelta, timezone
from typing import Optional
from uuid import UUID
from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from app.config import get_settings
from app.models.user import User, UserRole

settings = get_settings()
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def hash_password(password: str) -> str:
    return pwd_context.hash(password)

def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    payload = data.copy()
    expire = datetime.now(timezone.utc) + (expires_delta or timedelta(minutes=settings.access_token_expire_minutes))
    payload["exp"] = expire
    return jwt.encode(payload, settings.secret_key, algorithm=settings.algorithm)

def decode_token(token: str) -> dict:
    try:
        return jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm])
    except JWTError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")

def register_user(db: Session, email: str, full_name: str, password: str, role: UserRole = UserRole.VIEWER) -> User:
    if db.query(User).filter(User.email == email).first():
        raise HTTPException(status_code=400, detail="Email already registered")
    is_first_user = db.query(User).count() == 0
    user = User(
        email=email,
        full_name=full_name,
        hashed_password=hash_password(password),
        role=UserRole.SUPER_ADMIN if is_first_user else role,
        is_verified=is_first_user,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user

def authenticate_user(db: Session, email: str, password: str) -> User:
    user = db.query(User).filter(User.email == email).first()
    if not user or not verify_password(password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    if not user.is_active:
        raise HTTPException(status_code=403, detail="Account is inactive")
    if not user.is_verified:
        raise HTTPException(status_code=403, detail="Your account is pending admin approval.")
    return user

def get_current_user(db: Session, token: str) -> User:
    payload = decode_token(token)
    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(status_code=401, detail="Invalid token payload")
    try:
        user_id = UUID(str(user_id))
    except ValueError:
        raise HTTPException(status_code=401, detail="Invalid token payload")
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user

def list_pending_users(db: Session) -> list[User]:
    return db.query(User).filter(User.is_verified == False).order_by(User.created_at).all()

def list_all_users(db: Session) -> list[User]:
    return db.query(User).order_by(User.created_at).all()

def _get_user_or_404(db: Session, user_id) -> User:
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user

def _guard_admin_action(admin: User, target: User) -> None:
    """Common guards for admin mutations on another account."""
    if target.id == admin.id:
        raise HTTPException(status_code=400, detail="You cannot modify your own account here")
    if admin.role != UserRole.SUPER_ADMIN and target.role == UserRole.SUPER_ADMIN:
        raise HTTPException(status_code=403, detail="Only a super admin can modify a super admin account")

def approve_user(db: Session, user_id) -> User:
    user = _get_user_or_404(db, user_id)
    user.is_verified = True
    db.commit()
    db.refresh(user)
    return user

def reject_user(db: Session, admin: User, user_id) -> None:
    """Reject a pending signup by deleting the unverified account, freeing the
    email for re-registration. Verified accounts must be deactivated instead."""
    user = _get_user_or_404(db, user_id)
    _guard_admin_action(admin, user)
    if user.is_verified:
        raise HTTPException(status_code=409, detail="Account already approved — deactivate it instead")
    db.delete(user)
    db.commit()

def set_user_active(db: Session, admin: User, user_id, is_active: bool) -> User:
    user = _get_user_or_404(db, user_id)
    _guard_admin_action(admin, user)
    user.is_active = is_active
    db.commit()
    db.refresh(user)
    return user

def set_user_role(db: Session, admin: User, user_id, role: UserRole) -> User:
    user = _get_user_or_404(db, user_id)
    _guard_admin_action(admin, user)
    if role == UserRole.SUPER_ADMIN and admin.role != UserRole.SUPER_ADMIN:
        raise HTTPException(status_code=403, detail="Only a super admin can grant the super admin role")
    user.role = role
    db.commit()
    db.refresh(user)
    return user
