from __future__ import annotations

from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.core.security import create_access_token, hash_password, verify_password
from app.db.session import get_db
from app.models.wfm import AuditLog, Permission, Role, RolePermission, User

router = APIRouter(prefix="/api/v1/auth", tags=["auth"])


class LoginIn(BaseModel):
    username: str
    password: str


class ChangePasswordIn(BaseModel):
    old_password: str
    new_password: str = Field(min_length=10)


def user_permissions(db: Session, user: User) -> list[str]:
    if user.is_superuser:
        return [row.code for row in db.query(Permission).order_by(Permission.code).all()]
    if not user.role_id:
        return []
    return [
        row.code
        for row in db.query(Permission)
        .join(RolePermission, RolePermission.permission_id == Permission.id)
        .filter(RolePermission.role_id == user.role_id)
        .order_by(Permission.code)
        .all()
    ]


def user_payload(db: Session, user: User) -> dict:
    role = db.get(Role, user.role_id) if user.role_id else None
    return {
        "id": user.id,
        "email": user.email,
        "username": user.username,
        "full_name": user.full_name,
        "role": role.code if role else user.role,
        "permissions": user_permissions(db, user),
    }


def write_audit(db: Session, action: str, request: Request | None = None, user: User | None = None, entity_type: str = "auth", entity_id: str | None = None, details: str | None = None) -> None:
    db.add(AuditLog(
        actor_user_id=user.id if user else None,
        actor_username=user.username if user else None,
        actor=user.username if user else "anonymous",
        action=action,
        entity_type=entity_type,
        entity_id=entity_id,
        details=details,
        details_json=details,
        ip_address=request.client.host if request and request.client else None,
        user_agent=request.headers.get("user-agent") if request else None,
    ))
    db.commit()


@router.post("/login")
def login(payload: LoginIn, request: Request, db: Session = Depends(get_db)):
    user = db.query(User).filter((User.username == payload.username) | (User.email == payload.username)).first()
    if not user or not user.is_active or not verify_password(payload.password, user.password_hash):
        write_audit(db, "login_failed", request=request, details=f"username={payload.username}")
        raise HTTPException(status_code=401, detail="Неверный логин или пароль")
    user.last_login_at = datetime.utcnow()
    db.commit()
    write_audit(db, "login_success", request=request, user=user)
    return {
        "access_token": create_access_token(str(user.id), {"username": user.username}),
        "token_type": "bearer",
        "user": user_payload(db, user),
    }


@router.get("/me")
def me(request: Request, db: Session = Depends(get_db)):
    user = getattr(request.state, "user", None)
    if not user:
        raise HTTPException(status_code=401, detail="Требуется авторизация")
    return user_payload(db, user)


@router.post("/logout")
def logout():
    return {"status": "ok"}


@router.post("/change-password")
def change_password(payload: ChangePasswordIn, request: Request, db: Session = Depends(get_db)):
    user = getattr(request.state, "user", None)
    if not user:
        raise HTTPException(status_code=401, detail="Требуется авторизация")
    if not verify_password(payload.old_password, user.password_hash):
        raise HTTPException(status_code=400, detail="Старый пароль указан неверно")
    user.password_hash = hash_password(payload.new_password)
    db.commit()
    write_audit(db, "change_password", request=request, user=user, entity_type="user", entity_id=str(user.id))
    return {"status": "ok"}
