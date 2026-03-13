from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.deps import require_any_permission, require_permission
from app.models import Customer, Incident, IncidentSeverity, IncidentStatus, Ticket, User
from app.schemas import IncidentCommunicationUpdate, IncidentCreate, IncidentOut, IncidentUpdate
from app.services.audit import log_audit_event
from app.services.operations import (
    apply_incident_status_markers,
    incident_default_comm_interval,
    sync_incident_communication_due,
    utc_now,
)

router = APIRouter()


@router.get("", response_model=list[IncidentOut])
def list_incidents(
    status_filter: IncidentStatus | None = Query(default=None, alias="status"),
    severity: IncidentSeverity | None = Query(default=None),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_any_permission("incident.read", "incident.manage")),
) -> list[IncidentOut]:
    query = select(Incident).where(Incident.tenant_id == current_user.tenant_id).order_by(Incident.created_at.desc())
    if status_filter:
        query = query.where(Incident.status == status_filter)
    if severity:
        query = query.where(Incident.severity == severity)
    return list(db.scalars(query))


@router.post("", response_model=IncidentOut, status_code=status.HTTP_201_CREATED)
def create_incident(
    payload: IncidentCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("incident.manage")),
) -> IncidentOut:
    if payload.ticket_id:
        ticket = db.scalar(
            select(Ticket).where(Ticket.id == payload.ticket_id, Ticket.tenant_id == current_user.tenant_id)
        )
        if ticket is None:
            raise HTTPException(status_code=400, detail="Invalid ticket reference")
    if payload.customer_id:
        customer = db.scalar(
            select(Customer).where(
                Customer.id == payload.customer_id, Customer.tenant_id == current_user.tenant_id
            )
        )
        if customer is None:
            raise HTTPException(status_code=400, detail="Invalid customer reference")

    incident = Incident(
        tenant_id=current_user.tenant_id,
        ticket_id=payload.ticket_id,
        customer_id=payload.customer_id,
        title=payload.title,
        summary=payload.summary,
        severity=payload.severity,
        status=payload.status,
        is_major=payload.is_major,
        assigned_user_id=payload.assigned_user_id,
        communication_interval_minutes=payload.communication_interval_minutes
        or incident_default_comm_interval(payload.severity),
        created_by_user_id=current_user.id,
    )
    apply_incident_status_markers(incident)
    sync_incident_communication_due(incident, now=utc_now())
    db.add(incident)
    db.flush()
    log_audit_event(
        db,
        tenant_id=current_user.tenant_id,
        actor_user_id=current_user.id,
        action="incident.create",
        resource_type="incident",
        resource_id=incident.id,
        event_data={"severity": incident.severity.value, "status": incident.status.value},
    )
    db.commit()
    db.refresh(incident)
    return incident


@router.patch("/{incident_id}", response_model=IncidentOut)
def update_incident(
    incident_id: str,
    payload: IncidentUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("incident.manage")),
) -> IncidentOut:
    incident = db.scalar(
        select(Incident).where(Incident.id == incident_id, Incident.tenant_id == current_user.tenant_id)
    )
    if incident is None:
        raise HTTPException(status_code=404, detail="Incident not found")

    if payload.title is not None:
        incident.title = payload.title
    if payload.summary is not None:
        incident.summary = payload.summary
    if payload.severity is not None:
        incident.severity = payload.severity
        if payload.communication_interval_minutes is None:
            incident.communication_interval_minutes = incident_default_comm_interval(payload.severity)
    if payload.status is not None:
        incident.status = payload.status
    if payload.is_major is not None:
        incident.is_major = payload.is_major
    if payload.assigned_user_id is not None:
        incident.assigned_user_id = payload.assigned_user_id
    if payload.communication_interval_minutes is not None:
        incident.communication_interval_minutes = payload.communication_interval_minutes
    apply_incident_status_markers(incident)
    sync_incident_communication_due(incident, now=utc_now())

    log_audit_event(
        db,
        tenant_id=current_user.tenant_id,
        actor_user_id=current_user.id,
        action="incident.update",
        resource_type="incident",
        resource_id=incident.id,
        event_data=payload.model_dump(exclude_none=True, mode="json"),
    )
    db.commit()
    db.refresh(incident)
    return incident


@router.post("/{incident_id}/communications", response_model=IncidentOut)
def log_incident_communication(
    incident_id: str,
    payload: IncidentCommunicationUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("incident.manage")),
) -> IncidentOut:
    incident = db.scalar(
        select(Incident).where(Incident.id == incident_id, Incident.tenant_id == current_user.tenant_id)
    )
    if incident is None:
        raise HTTPException(status_code=404, detail="Incident not found")

    communication_at = utc_now()
    incident.last_communication_at = communication_at
    sync_incident_communication_due(incident, now=communication_at)

    log_audit_event(
        db,
        tenant_id=current_user.tenant_id,
        actor_user_id=current_user.id,
        action="incident.communication",
        resource_type="incident",
        resource_id=incident.id,
        event_data={
            "note": payload.note,
            "last_communication_at": communication_at.isoformat(),
            "next_communication_due_at": incident.next_communication_due_at.isoformat()
            if incident.next_communication_due_at
            else None,
        },
    )
    db.commit()
    db.refresh(incident)
    return incident
