from collections import Counter
from typing import Iterable

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import KnowledgeArticle, Runbook, Ticket, TicketStatus, User
from app.schemas import AiCopilotRecommendation


ROOT_CAUSE_HINTS: dict[str, str] = {
    "outage": "service_outage",
    "latency": "performance_degradation",
    "slow": "performance_degradation",
    "auth": "identity_access_issue",
    "login": "identity_access_issue",
    "password": "identity_access_issue",
    "backup": "backup_restore_issue",
    "patch": "change_related_issue",
    "deploy": "change_related_issue",
    "disk": "capacity_issue",
    "cpu": "capacity_issue",
    "memory": "capacity_issue",
    "network": "network_issue",
    "dns": "network_issue",
}


def _tokenize(value: str) -> set[str]:
    normalized = "".join(ch.lower() if ch.isalnum() else " " for ch in value)
    tokens = [token for token in normalized.split() if len(token) >= 3]
    return set(tokens)


def _score_text_match(query_tokens: set[str], *values: str) -> int:
    doc_tokens = set()
    for value in values:
        doc_tokens.update(_tokenize(value))
    return len(query_tokens.intersection(doc_tokens))


def infer_root_cause_category(query: str) -> str:
    query_tokens = _tokenize(query)
    hint_counts: Counter[str] = Counter()
    for token in query_tokens:
        category = ROOT_CAUSE_HINTS.get(token)
        if category:
            hint_counts[category] += 1
    if not hint_counts:
        return "unknown"
    return hint_counts.most_common(1)[0][0]


def rank_articles(
    query_tokens: set[str],
    articles: Iterable[KnowledgeArticle],
    max_results: int,
) -> list[KnowledgeArticle]:
    ranked = sorted(
        ((article, _score_text_match(query_tokens, article.title, article.body, " ".join(article.tags or []))) for article in articles),
        key=lambda pair: pair[1],
        reverse=True,
    )
    return [article for article, score in ranked if score > 0][:max_results]


def rank_tickets(query_tokens: set[str], tickets: Iterable[Ticket], max_results: int) -> list[Ticket]:
    ranked = sorted(
        ((ticket, _score_text_match(query_tokens, ticket.title, ticket.description or "")) for ticket in tickets),
        key=lambda pair: pair[1],
        reverse=True,
    )
    return [ticket for ticket, score in ranked if score > 0][:max_results]


def suggest_runbooks(query_tokens: set[str], runbooks: Iterable[Runbook], max_results: int) -> list[str]:
    ranked = sorted(
        (
            (
                runbook.name,
                _score_text_match(query_tokens, runbook.name, runbook.description or "", runbook.execution_template or ""),
            )
            for runbook in runbooks
        ),
        key=lambda pair: pair[1],
        reverse=True,
    )
    return [name for name, score in ranked if score > 0][:max_results]


def generate_recommendations(
    *,
    root_cause_category: str,
    suggested_runbooks: list[str],
    similar_ticket_count: int,
    article_count: int,
) -> list[AiCopilotRecommendation]:
    recommendations: list[AiCopilotRecommendation] = [
        AiCopilotRecommendation(
            title="Classify incident",
            confidence=0.65,
            rationale=f"Detected category '{root_cause_category}' from issue description keywords.",
        )
    ]
    if suggested_runbooks:
        recommendations.append(
            AiCopilotRecommendation(
                title="Execute standard runbook candidate",
                confidence=0.6,
                rationale=f"Matched runbook names: {', '.join(suggested_runbooks[:3])}.",
            )
        )
    if similar_ticket_count > 0:
        recommendations.append(
            AiCopilotRecommendation(
                title="Review historical tickets",
                confidence=0.55,
                rationale=f"Found {similar_ticket_count} similar ticket(s) for faster triage.",
            )
        )
    if article_count > 0:
        recommendations.append(
            AiCopilotRecommendation(
                title="Attach knowledge article",
                confidence=0.58,
                rationale=f"Found {article_count} relevant knowledge article(s).",
            )
        )
    return recommendations


def fetch_copilot_context(
    db: Session,
    *,
    user: User,
    include_closed: bool,
) -> tuple[list[Ticket], list[KnowledgeArticle], list[Runbook]]:
    tickets_query = select(Ticket).where(Ticket.tenant_id == user.tenant_id)
    if not include_closed:
        tickets_query = tickets_query.where(Ticket.status != TicketStatus.DONE)
    tickets = list(db.scalars(tickets_query.order_by(Ticket.created_at.desc()).limit(200)))

    articles = list(
        db.scalars(
            select(KnowledgeArticle)
            .where(KnowledgeArticle.tenant_id == user.tenant_id)
            .order_by(KnowledgeArticle.created_at.desc())
            .limit(200)
        )
    )
    runbooks = list(
        db.scalars(
            select(Runbook)
            .where(Runbook.tenant_id == user.tenant_id, Runbook.enabled.is_(True))
            .order_by(Runbook.created_at.desc())
            .limit(100)
        )
    )
    return tickets, articles, runbooks
