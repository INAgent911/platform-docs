from datetime import datetime, timedelta, timezone

from app.models import (
    Incident,
    IncidentSeverity,
    IncidentStatus,
    Ticket,
    TicketPriority,
    TicketStatus,
)


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _as_utc(dt: datetime | None) -> datetime | None:
    if dt is None:
        return None
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


TICKET_SLA_MINUTES: dict[TicketPriority, tuple[int, int]] = {
    TicketPriority.P1: (15, 4 * 60),
    TicketPriority.P2: (30, 8 * 60),
    TicketPriority.P3: (4 * 60, 2 * 24 * 60),
    TicketPriority.P4: (24 * 60, 5 * 24 * 60),
}


INCIDENT_COMM_MINUTES: dict[IncidentSeverity, int] = {
    IncidentSeverity.SEV1: 30,
    IncidentSeverity.SEV2: 60,
    IncidentSeverity.SEV3: 4 * 60,
    IncidentSeverity.SEV4: 24 * 60,
}


def apply_ticket_sla(ticket: Ticket, *, base_time: datetime | None = None) -> None:
    baseline = _as_utc(base_time) or _as_utc(ticket.created_at) or utc_now()
    response_minutes, resolve_minutes = TICKET_SLA_MINUTES[ticket.priority]
    ticket.response_due_at = baseline + timedelta(minutes=response_minutes)
    ticket.resolve_due_at = baseline + timedelta(minutes=resolve_minutes)


def apply_ticket_status_markers(ticket: Ticket, *, now: datetime | None = None) -> None:
    event_time = _as_utc(now) or utc_now()
    if ticket.status != TicketStatus.NEW and ticket.first_responded_at is None:
        ticket.first_responded_at = event_time
    if ticket.status == TicketStatus.DONE and ticket.resolved_at is None:
        ticket.resolved_at = event_time
    if ticket.status != TicketStatus.DONE:
        ticket.resolved_at = None

    if ticket.escalated_at is None and (
        (ticket.first_responded_at is None and ticket.response_due_at and event_time > ticket.response_due_at)
        or (ticket.resolved_at is None and ticket.resolve_due_at and event_time > ticket.resolve_due_at)
    ):
        ticket.escalated_at = event_time


def ticket_sla_state(ticket: Ticket, *, now: datetime | None = None) -> dict[str, bool]:
    event_time = _as_utc(now) or utc_now()
    response_due_at = _as_utc(ticket.response_due_at)
    resolve_due_at = _as_utc(ticket.resolve_due_at)
    response_breached = bool(
        response_due_at and ticket.first_responded_at is None and event_time > response_due_at
    )
    resolution_breached = bool(
        resolve_due_at and ticket.resolved_at is None and event_time > resolve_due_at
    )
    return {
        "response_breached": response_breached,
        "resolution_breached": resolution_breached,
        "is_escalated": bool(ticket.escalated_at or response_breached or resolution_breached),
    }


def incident_default_comm_interval(severity: IncidentSeverity) -> int:
    return INCIDENT_COMM_MINUTES[severity]


def sync_incident_communication_due(incident: Incident, *, now: datetime | None = None) -> None:
    event_time = _as_utc(now) or utc_now()
    incident.next_communication_due_at = event_time + timedelta(
        minutes=incident.communication_interval_minutes
    )


def apply_incident_status_markers(incident: Incident, *, now: datetime | None = None) -> None:
    event_time = _as_utc(now) or utc_now()
    if incident.status in {IncidentStatus.RESOLVED, IncidentStatus.CLOSED} and incident.resolved_at is None:
        incident.resolved_at = event_time
    if incident.status not in {IncidentStatus.RESOLVED, IncidentStatus.CLOSED}:
        incident.resolved_at = None
