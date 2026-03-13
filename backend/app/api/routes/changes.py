from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.deps import require_any_permission, require_permission
from app.models import ChangeRequest, ChangeStatus, ChangeType, Incident, Runbook, Ticket, User
from app.schemas import (
    ChangeApprovalRequest,
    ChangeExecutionUpdate,
    ChangeRequestCreate,
    ChangeRequestOut,
    ChangeRequestUpdate,
)
from app.services.audit import log_audit_event

router = APIRouter()


def _get_runbook(
    db: Session,
    current_user: User,
    runbook_id: str | None,
) -> Runbook | None:
    if runbook_id is None:
        return None
    runbook = db.scalar(
        select(Runbook).where(
            Runbook.id == runbook_id,
            Runbook.tenant_id == current_user.tenant_id,
            Runbook.enabled.is_(True),
        )
    )
    if runbook is None:
        raise HTTPException(status_code=400, detail="Invalid or disabled runbook reference")
    return runbook


def _validate_change_policy(
    *,
    change_type: ChangeType,
    risk_score: int,
    rollback_plan: str | None,
    runbook: Runbook | None,
) -> None:
    if change_type != ChangeType.STANDARD and runbook is not None:
        raise HTTPException(status_code=400, detail="Runbooks can only be linked to standard changes")
    if change_type in {ChangeType.NORMAL, ChangeType.EMERGENCY} and risk_score >= 7 and not rollback_plan:
        raise HTTPException(
            status_code=400,
            detail="Rollback plan is required for high-risk normal/emergency changes",
        )
    if runbook is not None and not (runbook.min_risk_score <= risk_score <= runbook.max_risk_score):
        raise HTTPException(status_code=400, detail="Risk score not allowed by selected runbook")


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
    runbook = _get_runbook(db, current_user, payload.runbook_id)
    _validate_change_policy(
        change_type=payload.change_type,
        risk_score=payload.risk_score,
        rollback_plan=payload.rollback_plan,
        runbook=runbook,
    )

    change = ChangeRequest(
        tenant_id=current_user.tenant_id,
        incident_id=payload.incident_id,
        ticket_id=payload.ticket_id,
        title=payload.title,
        description=payload.description,
        change_type=payload.change_type,
        risk_score=payload.risk_score,
        runbook_id=payload.runbook_id,
        rollback_plan=payload.rollback_plan,
        scheduled_start_at=payload.scheduled_start_at,
        scheduled_end_at=payload.scheduled_end_at,
        automated_approval=False,
        execution_status="not_executed",
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
        event_data={
            "change_type": change.change_type.value,
            "risk_score": change.risk_score,
            "runbook_id": change.runbook_id,
        },
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
    if payload.runbook_id is not None:
        runbook = _get_runbook(db, current_user, payload.runbook_id)
        _validate_change_policy(
            change_type=payload.change_type or change.change_type,
            risk_score=payload.risk_score or change.risk_score,
            rollback_plan=payload.rollback_plan if payload.rollback_plan is not None else change.rollback_plan,
            runbook=runbook,
        )
        change.runbook_id = payload.runbook_id
    else:
        _validate_change_policy(
            change_type=payload.change_type or change.change_type,
            risk_score=payload.risk_score or change.risk_score,
            rollback_plan=payload.rollback_plan if payload.rollback_plan is not None else change.rollback_plan,
            runbook=change.runbook,
        )

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
    _validate_change_policy(
        change_type=change.change_type,
        risk_score=change.risk_score,
        rollback_plan=change.rollback_plan,
        runbook=change.runbook,
    )

    if (
        change.change_type == ChangeType.STANDARD
        and change.runbook is not None
        and change.runbook.auto_approve_low_risk
        and change.runbook.min_risk_score <= change.risk_score <= change.runbook.max_risk_score
    ):
        change.status = ChangeStatus.APPROVED
        change.automated_approval = True
        change.approval_notes = "Auto-approved by runbook low-risk policy"
        action = "change.auto_approve"
    else:
        change.status = ChangeStatus.PENDING_APPROVAL
        change.automated_approval = False
        action = "change.submit_approval"
    log_audit_event(
        db,
        tenant_id=current_user.tenant_id,
        actor_user_id=current_user.id,
        action=action,
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
    if payload.approved and current_user.id == change.requested_by_user_id:
        raise HTTPException(status_code=403, detail="Requester cannot approve their own change")
    if payload.approved:
        _validate_change_policy(
            change_type=change.change_type,
            risk_score=change.risk_score,
            rollback_plan=change.rollback_plan,
            runbook=change.runbook,
        )

    change.status = ChangeStatus.APPROVED if payload.approved else ChangeStatus.REJECTED
    change.approved_by_user_id = current_user.id
    change.approval_notes = payload.approval_notes
    change.automated_approval = False
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


@router.post("/{change_id}/execute-runbook", response_model=ChangeRequestOut)
def execute_runbook_for_change(
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
    if change.change_type != ChangeType.STANDARD:
        raise HTTPException(status_code=400, detail="Runbook execution only supports standard changes")
    if change.status not in {ChangeStatus.APPROVED, ChangeStatus.IN_PROGRESS}:
        raise HTTPException(status_code=400, detail="Standard change must be approved before execution")

    runbook = _get_runbook(db, current_user, change.runbook_id)
    if runbook is None:
        raise HTTPException(status_code=400, detail="No runbook linked to this change")

    executed_at = datetime.now(timezone.utc)
    change.execution_status = "succeeded"
    change.execution_output = (
        f"Executed runbook '{runbook.name}' using template '{runbook.execution_template or 'default'}'"
    )
    change.executed_at = executed_at
    change.status = ChangeStatus.COMPLETED
    if change.scheduled_start_at is None:
        change.scheduled_start_at = executed_at
    if change.scheduled_end_at is None:
        change.scheduled_end_at = executed_at

    log_audit_event(
        db,
        tenant_id=current_user.tenant_id,
        actor_user_id=current_user.id,
        action="change.execute_runbook",
        resource_type="change_request",
        resource_id=change.id,
        event_data={"runbook_id": runbook.id, "execution_status": change.execution_status},
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
    change.execution_status = "rolled_back" if payload.rolled_back else "succeeded"
    if change.scheduled_end_at is None:
        change.scheduled_end_at = datetime.now(timezone.utc)
    if change.executed_at is None:
        change.executed_at = change.scheduled_end_at
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
