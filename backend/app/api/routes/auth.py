from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.security import create_access_token, get_password_hash, verify_password
from app.db.session import get_db
from app.deps import get_current_user
from app.models import Tenant, User, UserRole
from app.schemas import LoginRequest, OwnerRegistration, Token, UserOut
from app.services.audit import log_audit_event

router = APIRouter()


@router.post("/register-owner", response_model=UserOut, status_code=status.HTTP_201_CREATED)
def register_owner(payload: OwnerRegistration, db: Session = Depends(get_db)) -> UserOut:
    existing_tenant = db.scalar(select(Tenant).where(Tenant.slug == payload.tenant_slug))
    if existing_tenant:
        raise HTTPException(status_code=409, detail="Tenant slug already exists")

    tenant = Tenant(name=payload.tenant_name, slug=payload.tenant_slug)
    db.add(tenant)
    db.flush()

    user = User(
        tenant_id=tenant.id,
        email=payload.email,
        first_name=payload.first_name,
        last_name=payload.last_name,
        hashed_password=get_password_hash(payload.password),
        role=UserRole.OWNER,
        is_active=True,
    )
    db.add(user)
    db.flush()

    log_audit_event(
        db,
        tenant_id=tenant.id,
        actor_user_id=user.id,
        action="auth.owner_registered",
        resource_type="user",
        resource_id=user.id,
    )
    db.commit()
    db.refresh(user)
    return user


@router.post("/login", response_model=Token)
def login(payload: LoginRequest, db: Session = Depends(get_db)) -> Token:
    tenant = db.scalar(select(Tenant).where(Tenant.slug == payload.tenant_slug))
    if tenant is None:
        raise HTTPException(status_code=401, detail="Invalid credentials")

    user = db.scalar(select(User).where(User.tenant_id == tenant.id, User.email == payload.email))
    if user is None or not verify_password(payload.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    access_token = create_access_token(subject=user.id, tenant_id=tenant.id, role=user.role.value)

    log_audit_event(
        db,
        tenant_id=tenant.id,
        actor_user_id=user.id,
        action="auth.login",
        resource_type="session",
        resource_id=user.id,
    )
    db.commit()

    return Token(access_token=access_token)


@router.get("/me", response_model=UserOut)
def me(current_user: User = Depends(get_current_user)) -> UserOut:
    return current_user

