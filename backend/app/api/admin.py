from __future__ import annotations

from datetime import date, datetime, time

from fastapi import APIRouter, Depends, Request
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.core.security import hash_password
from app.db.session import get_db
from app.models.integration_settings import NaumenProject, UserProjectAccess
from app.models.wfm import AuditLog, ExportLog, Permission, Role, RolePermission, User

router = APIRouter(prefix="/api/v1", tags=["admin"])


class UserIn(BaseModel):
    email: str
    username: str | None = None
    full_name: str
    role_id: int
    is_active: bool = True
    is_superuser: bool = False
    password: str | None = Field(default=None, min_length=10)
    project_ids: list[int] = []
    can_sync_project_ids: list[int] = []


def role_code(db: Session, role_id: int | None) -> str:
    role = db.get(Role, role_id) if role_id else None
    return role.code if role else "readonly"


def ensure_not_last_admin(db: Session, user: User, payload: UserIn | None = None) -> None:
    will_be_admin = bool(payload and (payload.is_superuser or role_code(db, payload.role_id) == "admin") and payload.is_active)
    if will_be_admin:
        return
    active_admins = [
        row for row in db.query(User).all()
        if row.is_active and (row.is_superuser or row.role == "admin")
    ]
    if len(active_admins) <= 1 and user.id in {row.id for row in active_admins}:
        from fastapi import HTTPException
        raise HTTPException(status_code=400, detail="Нельзя отключить или понизить последнего администратора")


def replace_project_access(db: Session, user_id: int, project_ids: list[int], can_sync_ids: list[int] | None = None) -> None:
    db.query(UserProjectAccess).filter(UserProjectAccess.user_id == user_id).delete()
    can_sync_set = set(can_sync_ids or [])
    existing_ids = {row.id for row in db.query(NaumenProject).filter(NaumenProject.id.in_(project_ids)).all()}
    for project_id in existing_ids:
        db.add(UserProjectAccess(user_id=user_id, naumen_project_id=project_id, can_view=True, can_sync=project_id in can_sync_set))


@router.get("/roles")
def list_roles(db: Session = Depends(get_db)):
    roles = db.query(Role).order_by(Role.id).all()
    result = []
    for role in roles:
        permissions = [
            row.code
            for row in db.query(Permission)
            .join(RolePermission, RolePermission.permission_id == Permission.id)
            .filter(RolePermission.role_id == role.id)
            .order_by(Permission.code)
            .all()
        ]
        result.append({"id": role.id, "code": role.code, "name": role.name, "description": role.description, "permissions": permissions})
    return result


@router.get("/permissions")
def list_permissions(db: Session = Depends(get_db)):
    return [{"id": row.id, "code": row.code, "name": row.name, "description": row.description} for row in db.query(Permission).order_by(Permission.code).all()]


@router.get("/users")
def list_users(db: Session = Depends(get_db)):
    return [
        {
            "id": row.id,
            "email": row.email,
            "username": row.username,
            "full_name": row.full_name,
            "role_id": row.role_id,
            "role": role_code(db, row.role_id),
            "is_active": row.is_active,
            "is_superuser": row.is_superuser,
            "last_login_at": row.last_login_at,
            "project_ids": [item.naumen_project_id for item in db.query(UserProjectAccess).filter(UserProjectAccess.user_id == row.id).all()],
        }
        for row in db.query(User).order_by(User.id).all()
    ]


@router.post("/users")
def create_user(payload: UserIn, request: Request, db: Session = Depends(get_db)):
    if not payload.username or not payload.email:
        from fastapi import HTTPException
        raise HTTPException(status_code=422, detail="username и email обязательны")
    user = User(
        email=payload.email,
        username=payload.username,
        full_name=payload.full_name,
        role_id=payload.role_id,
        role=role_code(db, payload.role_id),
        is_active=payload.is_active,
        is_superuser=payload.is_superuser,
        password_hash=hash_password(payload.password or "ChangeMe123!"),
    )
    db.add(user)
    db.flush()
    replace_project_access(db, user.id, payload.project_ids, payload.can_sync_project_ids)
    db.add(AuditLog(actor_username=getattr(getattr(request, "state", None), "username", None), actor="system", action="create_user", entity_type="user", entity_id=str(user.id)))
    db.commit()
    return {"id": user.id, "status": "created"}


@router.put("/users/{user_id}")
def update_user(user_id: int, payload: UserIn, db: Session = Depends(get_db)):
    user = db.get(User, user_id)
    if not user:
        return {"status": "not_found"}
    ensure_not_last_admin(db, user, payload)
    user.email = payload.email
    user.username = payload.username
    user.full_name = payload.full_name
    user.role_id = payload.role_id
    user.role = role_code(db, payload.role_id)
    user.is_active = payload.is_active
    user.is_superuser = payload.is_superuser
    if payload.password:
        user.password_hash = hash_password(payload.password)
    replace_project_access(db, user.id, payload.project_ids, payload.can_sync_project_ids)
    db.add(AuditLog(actor="system", action="update_user", entity_type="user", entity_id=str(user.id)))
    db.commit()
    return {"status": "updated", "id": user.id}


@router.delete("/users/{user_id}")
def deactivate_user(user_id: int, db: Session = Depends(get_db)):
    user = db.get(User, user_id)
    if user:
        ensure_not_last_admin(db, user, None)
        user.is_active = False
        db.add(AuditLog(actor="system", action="deactivate_user", entity_type="user", entity_id=str(user.id)))
        db.commit()
    return {"status": "disabled", "id": user_id}


@router.get("/users/{user_id}")
def read_user(user_id: int, db: Session = Depends(get_db)):
    user = db.get(User, user_id)
    if not user:
        return {"status": "not_found"}
    return {
        "id": user.id,
        "email": user.email,
        "username": user.username,
        "full_name": user.full_name,
        "role_id": user.role_id,
        "role": role_code(db, user.role_id),
        "is_active": user.is_active,
        "is_superuser": user.is_superuser,
        "project_ids": [item.naumen_project_id for item in db.query(UserProjectAccess).filter(UserProjectAccess.user_id == user.id, UserProjectAccess.can_view.is_(True)).all()],
    }


class ResetPasswordIn(BaseModel):
    password: str = Field(min_length=10)


@router.post("/users/{user_id}/reset-password")
def reset_password(user_id: int, payload: ResetPasswordIn, db: Session = Depends(get_db)):
    user = db.get(User, user_id)
    if not user:
        return {"status": "not_found"}
    user.password_hash = hash_password(payload.password)
    db.add(AuditLog(actor="system", action="reset_password", entity_type="user", entity_id=str(user.id)))
    db.commit()
    return {"status": "updated", "id": user.id}


@router.get("/users/{user_id}/projects")
def user_projects(user_id: int, db: Session = Depends(get_db)):
    return [
        {
            "id": row.id,
            "user_id": row.user_id,
            "naumen_project_id": row.naumen_project_id,
            "can_view": row.can_view,
            "can_sync": row.can_sync,
        }
        for row in db.query(UserProjectAccess).filter(UserProjectAccess.user_id == user_id).order_by(UserProjectAccess.id).all()
    ]


class UserProjectsIn(BaseModel):
    project_ids: list[int] = []
    can_sync_project_ids: list[int] = []


@router.put("/users/{user_id}/projects")
def update_user_projects(user_id: int, payload: UserProjectsIn, db: Session = Depends(get_db)):
    if not db.get(User, user_id):
        return {"status": "not_found"}
    replace_project_access(db, user_id, payload.project_ids, payload.can_sync_project_ids)
    db.commit()
    return {"status": "updated", "id": user_id}


@router.put("/users/{user_id}/project-access")
def update_user_project_access(user_id: int, payload: UserProjectsIn, db: Session = Depends(get_db)):
    return update_user_projects(user_id, payload, db)


@router.post("/users/{user_id}/disable")
def disable_user(user_id: int, db: Session = Depends(get_db)):
    user = db.get(User, user_id)
    if not user:
        return {"status": "not_found"}
    ensure_not_last_admin(db, user, None)
    user.is_active = False
    db.add(AuditLog(actor="system", action="disable_user", entity_type="user", entity_id=str(user.id)))
    db.commit()
    return {"status": "disabled", "id": user.id}


@router.post("/users/{user_id}/enable")
def enable_user(user_id: int, db: Session = Depends(get_db)):
    user = db.get(User, user_id)
    if not user:
        return {"status": "not_found"}
    user.is_active = True
    db.add(AuditLog(actor="system", action="enable_user", entity_type="user", entity_id=str(user.id)))
    db.commit()
    return {"status": "enabled", "id": user.id}


@router.get("/audit-log")
def audit_log(date_from: date | None = None, date_to: date | None = None, actor: str | None = None, action: str | None = None, entity_type: str | None = None, limit: int = 100, db: Session = Depends(get_db)):
    query = db.query(AuditLog)
    if date_from:
        query = query.filter(AuditLog.created_at >= datetime.combine(date_from, time.min))
    if date_to:
        query = query.filter(AuditLog.created_at <= datetime.combine(date_to, time.max))
    if actor:
        query = query.filter(AuditLog.actor_username == actor)
    if action:
        query = query.filter(AuditLog.action == action)
    if entity_type:
        query = query.filter(AuditLog.entity_type == entity_type)
    return [
        {
            "id": row.id,
            "created_at": row.created_at,
            "actor": row.actor_username or row.actor,
            "action": row.action,
            "entity_type": row.entity_type,
            "entity_id": row.entity_id,
            "details": row.details_json or row.details,
        }
        for row in query.order_by(AuditLog.created_at.desc()).limit(limit).all()
    ]


@router.get("/reports/export-log")
def export_log(db: Session = Depends(get_db)):
    return [
        {"id": row.id, "user_id": row.user_id, "report_type": row.report_type, "filename": row.filename, "rows_count": row.rows_count, "created_at": row.created_at}
        for row in db.query(ExportLog).order_by(ExportLog.created_at.desc()).limit(100).all()
    ]
