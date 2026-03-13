from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.deps import require_any_permission, require_permission
from app.models import Customer, Ticket, TicketStatus, User
from app.schemas import TicketCreate, TicketOut, TicketUpdate
from app.services.audit import log_audit_event

router = APIRouter()


@router.get("", response_model=list[TicketOut])
def list_tickets(
    status_filter: TicketStatus | None = Query(default=None, alias="status"),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_any_permission("ticket.read", "ticket.manage")),
) -> list[TicketOut]:
    query = select(Ticket).where(Ticket.tenant_id == current_user.tenant_id).order_by(Ticket.created_at.desc())
    if status_filter is not None:
        query = query.where(Ticket.status == status_filter)
    return list(db.scalars(query))


@router.post("", response_model=TicketOut, status_code=status.HTTP_201_CREATED)
def create_ticket(
    payload: TicketCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("ticket.manage")),
) -> TicketOut:
    if payload.customer_id:
        customer = db.scalar(
            select(Customer).where(
                Customer.id == payload.customer_id, Customer.tenant_id == current_user.tenant_id
            )
        )
        if customer is None:
            raise HTTPException(status_code=400, detail="Invalid customer for this tenant")

    ticket = Ticket(
        tenant_id=current_user.tenant_id,
        title=payload.title,
        description=payload.description,
        customer_id=payload.customer_id,
        priority=payload.priority,
    )
    db.add(ticket)
    db.flush()
    log_audit_event(
        db,
        tenant_id=current_user.tenant_id,
        actor_user_id=current_user.id,
        action="ticket.create",
        resource_type="ticket",
        resource_id=ticket.id,
    )
    db.commit()
    db.refresh(ticket)
    return ticket


@router.patch("/{ticket_id}", response_model=TicketOut)
def update_ticket(
    ticket_id: str,
    payload: TicketUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("ticket.manage")),
) -> TicketOut:
    ticket = db.scalar(select(Ticket).where(Ticket.id == ticket_id, Ticket.tenant_id == current_user.tenant_id))
    if ticket is None:
        raise HTTPException(status_code=404, detail="Ticket not found")

    if payload.customer_id:
        customer = db.scalar(
            select(Customer).where(
                Customer.id == payload.customer_id, Customer.tenant_id == current_user.tenant_id
            )
        )
        if customer is None:
            raise HTTPException(status_code=400, detail="Invalid customer for this tenant")
        ticket.customer_id = payload.customer_id

    if payload.title is not None:
        ticket.title = payload.title
    if payload.description is not None:
        ticket.description = payload.description
    if payload.status is not None:
        ticket.status = payload.status
    if payload.priority is not None:
        ticket.priority = payload.priority

    log_audit_event(
        db,
        tenant_id=current_user.tenant_id,
        actor_user_id=current_user.id,
        action="ticket.update",
        resource_type="ticket",
        resource_id=ticket.id,
    )
    db.commit()
    db.refresh(ticket)
    return ticket
