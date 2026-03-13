from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.security import get_password_hash
from app.db.session import get_db
from app.deps import DEFAULT_ROLE_PERMISSIONS, get_current_user, require_permission, require_roles
from app.models import RolePermission, User, UserRole
from app.schemas import RolePermissionOut, UserActiveUpdate, UserCreate, UserOut, UserRoleUpdate
from app.services.audit import log_audit_event

router = APIRouter()


@router.get("/permissions", response_model=list[RolePermissionOut])
def list_permissions(
    current_user: User = Depends(require_permission("rbac.read")),
    db: Session = Depends(get_db),
) -> list[RolePermissionOut]:
    perms = list(db.scalars(select(RolePermission).order_by(RolePermission.role, RolePermission.permission)))
    if perms:
        return perms

    fallback: list[RolePermissionOut] = []
    for role, role_perms in DEFAULT_ROLE_PERMISSIONS.items():
        for perm in sorted(role_perms):
            fallback.append(
                RolePermissionOut(role=role, permission=perm, description=f"Default permission {perm}")
            )
    return fallback


@router.get("/users", response_model=list[UserOut])
def list_users(
    current_user: User = Depends(require_permission("rbac.read")),
    db: Session = Depends(get_db),
) -> list[UserOut]:
    return list(db.scalars(select(User).where(User.tenant_id == current_user.tenant_id).order_by(User.created_at)))


@router.post("/users", response_model=UserOut, status_code=status.HTTP_201_CREATED)
def create_user(
    payload: UserCreate,
    current_user: User = Depends(require_permission("rbac.manage")),
    db: Session = Depends(get_db),
) -> UserOut:
    existing = db.scalar(
        select(User).where(User.tenant_id == current_user.tenant_id, User.email == payload.email)
    )
    if existing:
        raise HTTPException(status_code=409, detail="User email already exists in tenant")

    if payload.role == UserRole.OWNER and current_user.role != UserRole.OWNER:
        raise HTTPException(status_code=403, detail="Only owner can assign owner role")

    user = User(
        tenant_id=current_user.tenant_id,
        email=payload.email,
        first_name=payload.first_name,
        last_name=payload.last_name,
        hashed_password=get_password_hash(payload.password),
        role=payload.role,
        mfa_enabled=payload.mfa_enabled,
        is_active=True,
    )
    db.add(user)
    db.flush()
    log_audit_event(
        db,
        tenant_id=current_user.tenant_id,
        actor_user_id=current_user.id,
        action="rbac.user_create",
        resource_type="user",
        resource_id=user.id,
        event_data={"email": payload.email, "role": payload.role.value},
    )
    db.commit()
    db.refresh(user)
    return user


@router.patch("/{user_id}/role", response_model=UserOut)
def update_user_role(
    user_id: str,
    payload: UserRoleUpdate,
    current_user: User = Depends(require_roles(UserRole.OWNER)),
    db: Session = Depends(get_db),
) -> UserOut:
    user = db.scalar(select(User).where(User.id == user_id, User.tenant_id == current_user.tenant_id))
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")

    if user.id == current_user.id and payload.role != UserRole.OWNER:
        raise HTTPException(status_code=400, detail="Owner cannot remove own owner role")

    user.role = payload.role
    log_audit_event(
        db,
        tenant_id=current_user.tenant_id,
        actor_user_id=current_user.id,
        action="rbac.user_role_update",
        resource_type="user",
        resource_id=user.id,
        event_data={"new_role": payload.role.value},
    )
    db.commit()
    db.refresh(user)
    return user


@router.patch("/{user_id}/active", response_model=UserOut)
def update_user_active(
    user_id: str,
    payload: UserActiveUpdate,
    current_user: User = Depends(require_permission("rbac.manage")),
    db: Session = Depends(get_db),
) -> UserOut:
    user = db.scalar(select(User).where(User.id == user_id, User.tenant_id == current_user.tenant_id))
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")

    if user.id == current_user.id and not payload.is_active:
        raise HTTPException(status_code=400, detail="Cannot deactivate your own account")

    if user.role == UserRole.OWNER and current_user.role != UserRole.OWNER:
        raise HTTPException(status_code=403, detail="Only owner can change owner active state")

    user.is_active = payload.is_active
    log_audit_event(
        db,
        tenant_id=current_user.tenant_id,
        actor_user_id=current_user.id,
        action="rbac.user_active_update",
        resource_type="user",
        resource_id=user.id,
        event_data={"is_active": payload.is_active},
    )
    db.commit()
    db.refresh(user)
    return user

