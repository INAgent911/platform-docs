from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.deps import require_any_permission, require_permission
from app.models import ChangeRequest, ChangeStatus, Incident, Ticket, User
from app.schemas import (
    ChangeApprovalRequest,
    ChangeExecutionUpdate,
    ChangeRequestCreate,
    ChangeRequestOut,
    ChangeRequestUpdate,
)
from app.services.audit import log_audit_event

router = APIRouter()


@router.get("", response_model=list[ChangeRequestOut])
def list_changes(
    status_filter: ChangeStatus | None = Query(default=None, alias="status"),
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_any_permission("change.read", "change.manage", "change.approve")
    ),
) -> list[ChangeRequestOut]:
    query = select(ChangeRequest).where(ChangeRequest.tenant_id == current_user.tenant_id).order_by(
        ChangeRequest.created_at.desc()
    )
    if status_filter:
        query = query.where(ChangeRequest.status == status_filter)
    return list(db.scalars(query))


@router.post("", response_model=ChangeRequestOut, status_code=status.HTTP_201_CREATED)
def create_change(
    payload: ChangeRequestCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("change.manage")),
) -> ChangeRequestOut:
    if payload.ticket_id:
        ticket = db.scalar(
            select(Ticket).where(Ticket.id == payload.ticket_id, Ticket.tenant_id == current_user.tenant_id)
        )
        if ticket is None:
            raise HTTPException(status_code=400, detail="Invalid ticket reference")
    if payload.incident_id:
        incident = db.scalar(
            select(Incident).where(
                Incident.id == payload.incident_id, Incident.tenant_id == current_user.tenant_id
            )
        )
        if incident is None:
            raise HTTPException(status_code=400, detail="Invalid incident reference")

    change = ChangeRequest(
        tenant_id=current_user.tenant_id,
        incident_id=payload.incident_id,
        ticket_id=payload.ticket_id,
        title=payload.title,
        description=payload.description,
        change_type=payload.change_type,
        risk_score=payload.risk_score,
        rollback_plan=payload.rollback_plan,
        scheduled_start_at=payload.scheduled_start_at,
        scheduled_end_at=payload.scheduled_end_at,
        requested_by_user_id=current_user.id,
    )
    db.add(change)
    db.flush()
    log_audit_event(
        db,
        tenant_id=current_user.tenant_id,
        actor_user_id=current_user.id,
        action="change.create",
        resource_type="change_request",
        resource_id=change.id,
        event_data={"change_type": change.change_type.value, "risk_score": change.risk_score},
    )
    db.commit()
    db.refresh(change)
    return change


@router.patch("/{change_id}", response_model=ChangeRequestOut)
def update_change(
    change_id: str,
    payload: ChangeRequestUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("change.manage")),
) -> ChangeRequestOut:
    change = db.scalar(
        select(ChangeRequest).where(
            ChangeRequest.id == change_id, ChangeRequest.tenant_id == current_user.tenant_id
        )
    )
    if change is None:
        raise HTTPException(status_code=404, detail="Change request not found")

    if payload.title is not None:
        change.title = payload.title
    if payload.description is not None:
        change.description = payload.description
    if payload.change_type is not None:
        change.change_type = payload.change_type
    if payload.risk_score is not None:
        change.risk_score = payload.risk_score
    if payload.rollback_plan is not None:
        change.rollback_plan = payload.rollback_plan
    if payload.scheduled_start_at is not None:
        change.scheduled_start_at = payload.scheduled_start_at
    if payload.scheduled_end_at is not None:
        change.scheduled_end_at = payload.scheduled_end_at
    if payload.status is not None:
        change.status = payload.status

    log_audit_event(
        db,
        tenant_id=current_user.tenant_id,
        actor_user_id=current_user.id,
        action="change.update",
        resource_type="change_request",
        resource_id=change.id,
        event_data=payload.model_dump(exclude_none=True, mode="json"),
    )
    db.commit()
    db.refresh(change)
    return change


@router.post("/{change_id}/submit-approval", response_model=ChangeRequestOut)
def submit_change_for_approval(
    change_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("change.manage")),
) -> ChangeRequestOut:
    change = db.scalar(
        select(ChangeRequest).where(
            ChangeRequest.id == change_id, ChangeRequest.tenant_id == current_user.tenant_id
        )
    )
    if change is None:
        raise HTTPException(status_code=404, detail="Change request not found")
    if change.status not in {ChangeStatus.DRAFT, ChangeStatus.REJECTED}:
        raise HTTPException(status_code=400, detail="Change request not in submittable state")

    change.status = ChangeStatus.PENDING_APPROVAL
    log_audit_event(
        db,
        tenant_id=current_user.tenant_id,
        actor_user_id=current_user.id,
        action="change.submit_approval",
        resource_type="change_request",
        resource_id=change.id,
    )
    db.commit()
    db.refresh(change)
    return change


@router.post("/{change_id}/approval", response_model=ChangeRequestOut)
def approve_or_reject_change(
    change_id: str,
    payload: ChangeApprovalRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("change.approve")),
) -> ChangeRequestOut:
    change = db.scalar(
        select(ChangeRequest).where(
            ChangeRequest.id == change_id, ChangeRequest.tenant_id == current_user.tenant_id
        )
    )
    if change is None:
        raise HTTPException(status_code=404, detail="Change request not found")
    if change.status != ChangeStatus.PENDING_APPROVAL:
        raise HTTPException(status_code=400, detail="Change request is not awaiting approval")

    change.status = ChangeStatus.APPROVED if payload.approved else ChangeStatus.REJECTED
    change.approved_by_user_id = current_user.id
    change.approval_notes = payload.approval_notes
    log_audit_event(
        db,
        tenant_id=current_user.tenant_id,
        actor_user_id=current_user.id,
        action="change.approval",
        resource_type="change_request",
        resource_id=change.id,
        event_data={"approved": payload.approved},
    )
    db.commit()
    db.refresh(change)
    return change


@router.post("/{change_id}/start", response_model=ChangeRequestOut)
def start_change(
    change_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("change.manage")),
) -> ChangeRequestOut:
    change = db.scalar(
        select(ChangeRequest).where(
            ChangeRequest.id == change_id, ChangeRequest.tenant_id == current_user.tenant_id
        )
    )
    if change is None:
        raise HTTPException(status_code=404, detail="Change request not found")
    if change.status not in {ChangeStatus.APPROVED, ChangeStatus.SCHEDULED}:
        raise HTTPException(status_code=400, detail="Change request is not approved or scheduled")

    change.status = ChangeStatus.IN_PROGRESS
    if change.scheduled_start_at is None:
        change.scheduled_start_at = datetime.now(timezone.utc)
    log_audit_event(
        db,
        tenant_id=current_user.tenant_id,
        actor_user_id=current_user.id,
        action="change.start",
        resource_type="change_request",
        resource_id=change.id,
    )
    db.commit()
    db.refresh(change)
    return change


@router.post("/{change_id}/complete", response_model=ChangeRequestOut)
def complete_change(
    change_id: str,
    payload: ChangeExecutionUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("change.manage")),
) -> ChangeRequestOut:
    change = db.scalar(
        select(ChangeRequest).where(
            ChangeRequest.id == change_id, ChangeRequest.tenant_id == current_user.tenant_id
        )
    )
    if change is None:
        raise HTTPException(status_code=404, detail="Change request not found")
    if change.status != ChangeStatus.IN_PROGRESS:
        raise HTTPException(status_code=400, detail="Change request must be in progress")

    change.status = ChangeStatus.ROLLED_BACK if payload.rolled_back else ChangeStatus.COMPLETED
    if change.scheduled_end_at is None:
        change.scheduled_end_at = datetime.now(timezone.utc)
    log_audit_event(
        db,
        tenant_id=current_user.tenant_id,
        actor_user_id=current_user.id,
        action="change.complete",
        resource_type="change_request",
        resource_id=change.id,
        event_data={"rolled_back": payload.rolled_back},
    )
    db.commit()
    db.refresh(change)
    return change

