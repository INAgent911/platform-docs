from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.deps import require_permission
from app.models import AlertEvent, Ticket, TicketPriority, User
from app.schemas import AlertEventOut, CloudEventIn, TicketOut
from app.services.audit import log_audit_event

router = APIRouter()


@router.post("", response_model=AlertEventOut, status_code=status.HTTP_201_CREATED)
def ingest_event(
    payload: CloudEventIn,
    create_ticket: bool = Query(default=False),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("event.ingest")),
) -> AlertEventOut:
    severity = payload.data.get("severity") if isinstance(payload.data, dict) else None
    event = AlertEvent(
        tenant_id=current_user.tenant_id,
        event_type=payload.type,
        source=payload.source,
        severity=severity,
        subject=payload.subject,
        external_event_id=payload.id,
        payload=payload.model_dump(mode="json"),
        occurred_at=payload.time,
    )
    db.add(event)
    db.flush()

    if create_ticket:
        summary = payload.data.get("summary") if isinstance(payload.data, dict) else payload.subject or payload.type
        ticket = Ticket(
            tenant_id=current_user.tenant_id,
            title=f"[Auto] {summary}",
            description=f"Auto-created from event {payload.id}",
            priority=TicketPriority.P2 if severity in {"critical", "high"} else TicketPriority.P3,
        )
        db.add(ticket)
        db.flush()
        log_audit_event(
            db,
            tenant_id=current_user.tenant_id,
            actor_user_id=current_user.id,
        action="event.ticket_auto_create",
        resource_type="ticket",
        resource_id=ticket.id,
        event_data={"event_id": event.id},
        )

    log_audit_event(
        db,
        tenant_id=current_user.tenant_id,
        actor_user_id=current_user.id,
        action="event.ingest",
        resource_type="alert_event",
        resource_id=event.id,
        event_data={"external_event_id": payload.id},
    )
    db.commit()
    db.refresh(event)
    return event


@router.post("/{event_id}/tickets", response_model=TicketOut, status_code=status.HTTP_201_CREATED)
def create_ticket_from_event(
    event_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("event.ingest")),
) -> TicketOut:
    event = db.get(AlertEvent, event_id)
    if not event or event.tenant_id != current_user.tenant_id:
        raise HTTPException(status_code=404, detail="Event not found")

    summary = event.payload.get("data", {}).get("summary") if isinstance(event.payload, dict) else event.subject
    severity = event.severity or ""
    ticket = Ticket(
        tenant_id=current_user.tenant_id,
        title=f"[Event] {summary or event.event_type}",
        description=f"Linked event: {event.external_event_id}",
        priority=TicketPriority.P2 if severity in {"critical", "high"} else TicketPriority.P3,
    )
    db.add(ticket)
    db.flush()
    log_audit_event(
        db,
        tenant_id=current_user.tenant_id,
        actor_user_id=current_user.id,
        action="event.ticket_create",
        resource_type="ticket",
        resource_id=ticket.id,
        event_data={"event_id": event.id},
    )
    db.commit()
    db.refresh(ticket)
    return ticket
