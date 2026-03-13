from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.deps import require_permission
from app.models import Runbook, User
from app.schemas import RunbookCreate, RunbookOut
from app.services.audit import log_audit_event
from app.services.usage import log_usage_event

router = APIRouter()


@router.get("", response_model=list[RunbookOut])
def list_runbooks(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("change.manage")),
) -> list[RunbookOut]:
    query = (
        select(Runbook)
        .where(Runbook.tenant_id == current_user.tenant_id)
        .order_by(Runbook.created_at.desc())
    )
    return list(db.scalars(query))


@router.post("", response_model=RunbookOut, status_code=status.HTTP_201_CREATED)
def create_runbook(
    payload: RunbookCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("change.manage")),
) -> RunbookOut:
    if payload.min_risk_score > payload.max_risk_score:
        raise HTTPException(status_code=400, detail="min_risk_score cannot exceed max_risk_score")

    existing = db.scalar(
        select(Runbook).where(
            Runbook.tenant_id == current_user.tenant_id,
            Runbook.name == payload.name,
        )
    )
    if existing is not None:
        raise HTTPException(status_code=409, detail="Runbook name already exists")

    runbook = Runbook(
        tenant_id=current_user.tenant_id,
        name=payload.name,
        description=payload.description,
        auto_approve_low_risk=payload.auto_approve_low_risk,
        min_risk_score=payload.min_risk_score,
        max_risk_score=payload.max_risk_score,
        execution_template=payload.execution_template,
        created_by_user_id=current_user.id,
    )
    db.add(runbook)
    db.flush()
    log_usage_event(
        db,
        tenant_id=current_user.tenant_id,
        actor_user_id=current_user.id,
        event_type="runbook.create",
    )
    log_audit_event(
        db,
        tenant_id=current_user.tenant_id,
        actor_user_id=current_user.id,
        action="runbook.create",
        resource_type="runbook",
        resource_id=runbook.id,
        event_data={
            "name": runbook.name,
            "auto_approve_low_risk": runbook.auto_approve_low_risk,
            "min_risk_score": runbook.min_risk_score,
            "max_risk_score": runbook.max_risk_score,
        },
    )
    db.commit()
    db.refresh(runbook)
    return runbook
