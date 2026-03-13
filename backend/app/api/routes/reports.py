from datetime import datetime, timezone

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.deps import require_permission
from app.models import ChangeRequest, ChangeStatus, Incident, IncidentStatus, Ticket, TicketStatus, UsageEvent, User
from app.schemas import OpsReportOut, UsageEventOut, UsageReportOut

router = APIRouter()


def _minutes_between(start: datetime, end: datetime) -> int:
    if start.tzinfo is None:
        start = start.replace(tzinfo=timezone.utc)
    if end.tzinfo is None:
        end = end.replace(tzinfo=timezone.utc)
    return max(0, int((end - start).total_seconds() // 60))


@router.get("/operations", response_model=OpsReportOut)
def operations_report(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("reports.read")),
) -> OpsReportOut:
    tickets = list(db.scalars(select(Ticket).where(Ticket.tenant_id == current_user.tenant_id)))
    incidents = list(db.scalars(select(Incident).where(Incident.tenant_id == current_user.tenant_id)))
    changes = list(db.scalars(select(ChangeRequest).where(ChangeRequest.tenant_id == current_user.tenant_id)))
    now = datetime.now(timezone.utc)

    tickets_open = sum(1 for ticket in tickets if ticket.status != TicketStatus.DONE)
    tickets_overdue = sum(
        1
        for ticket in tickets
        if ticket.status != TicketStatus.DONE
        and ((ticket.resolve_due_at is not None and now > ticket.resolve_due_at) or ticket.escalated_at is not None)
    )
    incidents_open = sum(1 for incident in incidents if incident.status not in {IncidentStatus.RESOLVED, IncidentStatus.CLOSED})
    incidents_major_open = sum(
        1
        for incident in incidents
        if incident.is_major and incident.status not in {IncidentStatus.RESOLVED, IncidentStatus.CLOSED}
    )
    changes_pending_approval = sum(1 for change in changes if change.status == ChangeStatus.PENDING_APPROVAL)
    changes_failed_or_rollback = sum(1 for change in changes if change.status == ChangeStatus.ROLLED_BACK)

    mttr_samples = [
        _minutes_between(ticket.created_at, ticket.resolved_at)
        for ticket in tickets
        if ticket.resolved_at is not None
    ]
    mttr_minutes = int(sum(mttr_samples) / len(mttr_samples)) if mttr_samples else None

    return OpsReportOut(
        tickets_open=tickets_open,
        tickets_overdue=tickets_overdue,
        incidents_open=incidents_open,
        incidents_major_open=incidents_major_open,
        changes_pending_approval=changes_pending_approval,
        changes_failed_or_rollback=changes_failed_or_rollback,
        mttr_minutes=mttr_minutes,
    )


@router.get("/usage", response_model=UsageReportOut)
def usage_report(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("reports.read")),
) -> UsageReportOut:
    events = list(
        db.scalars(
            select(UsageEvent)
            .where(UsageEvent.tenant_id == current_user.tenant_id)
            .order_by(UsageEvent.created_at.desc())
        )
    )
    by_event_type: dict[str, int] = {}
    total_units = 0
    total_cost_micros = 0
    for event in events:
        by_event_type[event.event_type] = by_event_type.get(event.event_type, 0) + event.units
        total_units += event.units
        total_cost_micros += event.cost_estimate_usd_micros

    return UsageReportOut(
        total_events=len(events),
        total_units=total_units,
        total_estimated_cost_usd=round(total_cost_micros / 1_000_000, 4),
        by_event_type=by_event_type,
    )


@router.get("/usage/events", response_model=list[UsageEventOut])
def usage_events(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("reports.read")),
) -> list[UsageEventOut]:
    query = (
        select(UsageEvent)
        .where(UsageEvent.tenant_id == current_user.tenant_id)
        .order_by(UsageEvent.created_at.desc())
        .limit(200)
    )
    return list(db.scalars(query))
