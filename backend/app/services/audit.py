from sqlalchemy.orm import Session

from app.models import AuditEvent


def log_audit_event(
    db: Session,
    *,
    tenant_id: str,
    actor_user_id: str | None,
    action: str,
    resource_type: str,
    resource_id: str | None = None,
    event_data: dict | None = None,
) -> AuditEvent:
    event = AuditEvent(
        tenant_id=tenant_id,
        actor_user_id=actor_user_id,
        action=action,
        resource_type=resource_type,
        resource_id=resource_id,
        event_data=event_data or {},
    )
    db.add(event)
    db.flush()
    return event
