from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.deps import require_permission
from app.models import User
from app.schemas import AiCopilotRequest, AiCopilotResultOut
from app.services.ai_copilot import (
    _tokenize,
    fetch_copilot_context,
    generate_recommendations,
    infer_root_cause_category,
    rank_articles,
    rank_tickets,
    suggest_runbooks,
)
from app.services.audit import log_audit_event
from app.services.usage import log_usage_event

router = APIRouter()


@router.post("/copilot", response_model=AiCopilotResultOut)
def copilot_assist(
    payload: AiCopilotRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("ai.assist")),
) -> AiCopilotResultOut:
    query_tokens = _tokenize(payload.query)
    tickets, articles, runbooks = fetch_copilot_context(
        db,
        user=current_user,
        include_closed=payload.include_closed,
    )
    recommended_articles = rank_articles(query_tokens, articles, payload.max_results)
    similar_tickets = rank_tickets(query_tokens, tickets, payload.max_results)
    suggested_runbook_names = suggest_runbooks(query_tokens, runbooks, payload.max_results)
    root_cause_category = infer_root_cause_category(payload.query)
    recommendations = generate_recommendations(
        root_cause_category=root_cause_category,
        suggested_runbooks=suggested_runbook_names,
        similar_ticket_count=len(similar_tickets),
        article_count=len(recommended_articles),
    )

    log_usage_event(
        db,
        tenant_id=current_user.tenant_id,
        actor_user_id=current_user.id,
        event_type="ai.copilot.query",
        units=max(1, len(payload.query) // 30),
        cost_estimate_usd_micros=max(10_000, len(payload.query) * 300),
        event_metadata={"max_results": payload.max_results},
    )
    log_audit_event(
        db,
        tenant_id=current_user.tenant_id,
        actor_user_id=current_user.id,
        action="ai.copilot_query",
        resource_type="assistant",
        resource_id=None,
        event_data={"query_length": len(payload.query), "root_cause_category": root_cause_category},
    )
    db.commit()

    return AiCopilotResultOut(
        root_cause_category=root_cause_category,
        suggested_runbooks=suggested_runbook_names,
        recommended_articles=recommended_articles,
        similar_tickets=similar_tickets,
        recommendations=recommendations,
    )
