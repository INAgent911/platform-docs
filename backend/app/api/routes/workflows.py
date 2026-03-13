from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.deps import require_permission
from app.models import ChangeRequest, ChangeStatus, ChangeType, Incident, IncidentStatus, Ticket, TicketStatus, User
from app.schemas import WorkflowRunOut, WorkflowTemplateOut
from app.services.audit import log_audit_event
from app.services.usage import log_usage_event

router = APIRouter()

WORKFLOW_TEMPLATES = [
    {
        "id": "stale_ticket_escalation",
        "name": "Stale Ticket Escalation",
        "description": "Escalate tickets with breached SLA response or resolution windows.",
    },
    {
        "id": "incident_communication_reminder",
        "name": "Incident Communication Reminder",
        "description": "Identify incidents overdue for stakeholder communication updates.",
    },
    {
        "id": "standard_change_auto_approval",
        "name": "Standard Change Auto Approval",
        "description": "Auto-approve low-risk standard changes that match runbook policy.",
    },
]


@router.get("/templates", response_model=list[WorkflowTemplateOut])
def list_workflow_templates(
    _: User = Depends(require_permission("workflow.execute")),
) -> list[WorkflowTemplateOut]:
    return [WorkflowTemplateOut(**template) for template in WORKFLOW_TEMPLATES]


@router.post("/templates/{template_id}/run", response_model=WorkflowRunOut)
def run_workflow_template(
    template_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("workflow.execute")),
) -> WorkflowRunOut:
    now = datetime.now(timezone.utc)
    affected = 0
    summary = ""

    if template_id == "stale_ticket_escalation":
        tickets = list(
            db.scalars(
                select(Ticket).where(
                    Ticket.tenant_id == current_user.tenant_id,
                    Ticket.status != TicketStatus.DONE,
                )
            )
        )
        for ticket in tickets:
            if ticket.escalated_at is not None:
                continue
            response_breached = ticket.response_due_at is not None and ticket.first_responded_at is None and now > ticket.response_due_at
            resolution_breached = ticket.resolve_due_at is not None and ticket.resolved_at is None and now > ticket.resolve_due_at
            if response_breached or resolution_breached:
                ticket.escalated_at = now
                affected += 1
        summary = f"Escalated {affected} stale ticket(s)."

    elif template_id == "incident_communication_reminder":
        incidents = list(
            db.scalars(
                select(Incident).where(
                    Incident.tenant_id == current_user.tenant_id,
                    Incident.status.in_([IncidentStatus.OPEN, IncidentStatus.INVESTIGATING, IncidentStatus.MITIGATED]),
                )
            )
        )
        affected = sum(
            1
            for incident in incidents
            if incident.next_communication_due_at is not None and now > incident.next_communication_due_at
        )
        summary = f"Found {affected} incident(s) overdue for communication updates."

    elif template_id == "standard_change_auto_approval":
        pending_changes = list(
            db.scalars(
                select(ChangeRequest).where(
                    ChangeRequest.tenant_id == current_user.tenant_id,
                    ChangeRequest.status == ChangeStatus.PENDING_APPROVAL,
                    ChangeRequest.change_type == ChangeType.STANDARD,
                )
            )
        )
        for change in pending_changes:
            if (
                change.runbook
                and change.runbook.auto_approve_low_risk
                and change.runbook.min_risk_score <= change.risk_score <= change.runbook.max_risk_score
            ):
                change.status = ChangeStatus.APPROVED
                change.automated_approval = True
                change.approval_notes = "Approved by workflow template standard_change_auto_approval"
                affected += 1
        summary = f"Auto-approved {affected} standard change request(s)."

    else:
        raise HTTPException(status_code=404, detail="Unknown workflow template")

    log_usage_event(
        db,
        tenant_id=current_user.tenant_id,
        actor_user_id=current_user.id,
        event_type=f"workflow.run.{template_id}",
        units=max(1, affected),
    )
    log_audit_event(
        db,
        tenant_id=current_user.tenant_id,
        actor_user_id=current_user.id,
        action="workflow.run",
        resource_type="workflow_template",
        resource_id=template_id,
        event_data={"affected_records": affected, "summary": summary},
    )
    db.commit()

    return WorkflowRunOut(
        template_id=template_id,
        executed_at=now,
        summary=summary,
        affected_records=affected,
    )
