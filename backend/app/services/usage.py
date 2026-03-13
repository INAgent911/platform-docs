from sqlalchemy.orm import Session

from app.models import UsageEvent


def log_usage_event(
    db: Session,
    *,
    tenant_id: str,
    actor_user_id: str | None,
    event_type: str,
    units: int = 1,
    cost_estimate_usd_micros: int = 0,
    event_metadata: dict | None = None,
) -> UsageEvent:
    usage = UsageEvent(
        tenant_id=tenant_id,
        actor_user_id=actor_user_id,
        event_type=event_type,
        units=units,
        cost_estimate_usd_micros=cost_estimate_usd_micros,
        event_metadata=event_metadata or {},
    )
    db.add(usage)
    return usage
