from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.security import get_password_hash
from app.models import Tenant, User, UserRole
from app.services.audit import log_audit_event


def bootstrap_owner_if_needed(db: Session) -> None:
    settings = get_settings()
    if not settings.bootstrap_enabled:
        return

    tenant = db.scalar(select(Tenant).where(Tenant.slug == settings.bootstrap_tenant_slug))
    if tenant is None:
        tenant = Tenant(name=settings.bootstrap_tenant_name, slug=settings.bootstrap_tenant_slug)
        db.add(tenant)
        db.flush()

    owner = db.scalar(
        select(User).where(User.tenant_id == tenant.id, User.email == settings.bootstrap_owner_email)
    )
    if owner is not None:
        return

    owner = User(
        tenant_id=tenant.id,
        email=settings.bootstrap_owner_email,
        first_name=settings.bootstrap_owner_first_name,
        last_name=settings.bootstrap_owner_last_name,
        hashed_password=get_password_hash(settings.bootstrap_owner_password),
        role=UserRole.OWNER,
        is_active=True,
    )
    db.add(owner)
    db.flush()

    log_audit_event(
        db,
        tenant_id=tenant.id,
        actor_user_id=owner.id,
        action="bootstrap.owner_created",
        resource_type="user",
        resource_id=owner.id,
        event_data={"email": owner.email},
    )
