from collections.abc import Callable

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.security import decode_token
from app.db.session import get_db
from app.models import RolePermission, User, UserRole

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")


DEFAULT_ROLE_PERMISSIONS: dict[UserRole, set[str]] = {
    UserRole.OWNER: {
        "rbac.manage",
        "schema.manage",
        "incident.manage",
        "change.manage",
        "change.approve",
        "provisioning.manage",
        "ui.manage",
        "asset.manage",
        "asset.read",
        "knowledge.manage",
        "knowledge.read",
        "ai.assist",
        "workflow.execute",
        "reports.read",
        "customer.manage",
        "ticket.manage",
        "event.ingest",
    },
    UserRole.ADMIN: {
        "rbac.read",
        "rbac.manage",
        "schema.manage",
        "incident.manage",
        "change.manage",
        "change.approve",
        "provisioning.manage",
        "ui.manage",
        "asset.manage",
        "asset.read",
        "knowledge.manage",
        "knowledge.read",
        "ai.assist",
        "workflow.execute",
        "reports.read",
        "customer.manage",
        "ticket.manage",
        "event.ingest",
    },
    UserRole.USER: {
        "customer.read",
        "ticket.manage",
        "event.ingest",
        "incident.read",
        "change.read",
        "asset.read",
        "knowledge.read",
        "ai.assist",
    },
}


def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = decode_token(token)
        user_id = payload.get("sub")
        tenant_id = payload.get("tenant_id")
        if not user_id or not tenant_id:
            raise credentials_exception
    except ValueError as exc:
        raise credentials_exception from exc

    user = db.scalar(select(User).where(User.id == user_id, User.tenant_id == tenant_id))
    if user is None or not user.is_active:
        raise credentials_exception
    return user


def require_roles(*allowed_roles: UserRole) -> Callable[[User], User]:
    def checker(current_user: User = Depends(get_current_user)) -> User:
        if current_user.role not in allowed_roles:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient role")
        return current_user

    return checker


def _resolve_permissions(db: Session, role: UserRole) -> set[str]:
    role_perms = db.scalars(select(RolePermission.permission).where(RolePermission.role == role)).all()
    if role_perms:
        return set(role_perms)
    return DEFAULT_ROLE_PERMISSIONS.get(role, set())


def get_user_permissions(db: Session, user: User) -> set[str]:
    return _resolve_permissions(db, user.role)


def require_permission(permission: str) -> Callable[[Session, User], User]:
    def checker(
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user),
    ) -> User:
        permissions = _resolve_permissions(db, current_user.role)
        if permission not in permissions and current_user.role != UserRole.OWNER:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient permission")
        return current_user

    return checker


def require_any_permission(*permissions: str) -> Callable[[Session, User], User]:
    def checker(
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user),
    ) -> User:
        user_permissions = get_user_permissions(db, current_user)
        if current_user.role == UserRole.OWNER:
            return current_user
        if not any(permission in user_permissions for permission in permissions):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient permission")
        return current_user

    return checker
