from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.deps import require_any_permission, require_permission
from app.models import Customer, CustomerStatus, User
from app.schemas import CustomerCreate, CustomerOut, CustomerUpdate
from app.services.audit import log_audit_event

router = APIRouter()


@router.get("", response_model=list[CustomerOut])
def list_customers(
    status_filter: CustomerStatus | None = Query(default=None, alias="status"),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_any_permission("customer.read", "customer.manage")),
) -> list[CustomerOut]:
    query = select(Customer).where(Customer.tenant_id == current_user.tenant_id).order_by(Customer.created_at.desc())
    if status_filter:
        query = query.where(Customer.status == status_filter)
    return list(db.scalars(query))


@router.post("", response_model=CustomerOut, status_code=status.HTTP_201_CREATED)
def create_customer(
    payload: CustomerCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("customer.manage")),
) -> CustomerOut:
    customer = Customer(
        tenant_id=current_user.tenant_id,
        name=payload.name,
        status=payload.status,
        notes=payload.notes,
    )
    db.add(customer)
    db.flush()
    log_audit_event(
        db,
        tenant_id=current_user.tenant_id,
        actor_user_id=current_user.id,
        action="customer.create",
        resource_type="customer",
        resource_id=customer.id,
    )
    db.commit()
    db.refresh(customer)
    return customer


@router.patch("/{customer_id}", response_model=CustomerOut)
def update_customer(
    customer_id: str,
    payload: CustomerUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("customer.manage")),
) -> CustomerOut:
    customer = db.scalar(
        select(Customer).where(Customer.id == customer_id, Customer.tenant_id == current_user.tenant_id)
    )
    if customer is None:
        raise HTTPException(status_code=404, detail="Customer not found")

    if payload.name is not None:
        customer.name = payload.name
    if payload.status is not None:
        customer.status = payload.status
    if payload.notes is not None:
        customer.notes = payload.notes

    log_audit_event(
        db,
        tenant_id=current_user.tenant_id,
        actor_user_id=current_user.id,
        action="customer.update",
        resource_type="customer",
        resource_id=customer.id,
    )
    db.commit()
    db.refresh(customer)
    return customer
