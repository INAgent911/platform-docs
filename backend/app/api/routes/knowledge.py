from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.deps import require_any_permission, require_permission
from app.models import EntityKnowledgeLink, Incident, KnowledgeArticle, Ticket, User
from app.schemas import (
    EntityKnowledgeLinkCreate,
    EntityKnowledgeLinkOut,
    KnowledgeArticleCreate,
    KnowledgeArticleOut,
)
from app.services.audit import log_audit_event
from app.services.usage import log_usage_event

router = APIRouter()


@router.get("/articles", response_model=list[KnowledgeArticleOut])
def list_articles(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_any_permission("knowledge.read", "knowledge.manage")),
) -> list[KnowledgeArticleOut]:
    query = (
        select(KnowledgeArticle)
        .where(KnowledgeArticle.tenant_id == current_user.tenant_id)
        .order_by(KnowledgeArticle.created_at.desc())
    )
    return list(db.scalars(query))


@router.post("/articles", response_model=KnowledgeArticleOut, status_code=status.HTTP_201_CREATED)
def create_article(
    payload: KnowledgeArticleCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("knowledge.manage")),
) -> KnowledgeArticleOut:
    article = KnowledgeArticle(
        tenant_id=current_user.tenant_id,
        title=payload.title,
        body=payload.body,
        tags=payload.tags,
        known_error_code=payload.known_error_code,
        created_by_user_id=current_user.id,
    )
    db.add(article)
    db.flush()
    log_usage_event(
        db,
        tenant_id=current_user.tenant_id,
        actor_user_id=current_user.id,
        event_type="knowledge.article.create",
    )
    log_audit_event(
        db,
        tenant_id=current_user.tenant_id,
        actor_user_id=current_user.id,
        action="knowledge.article_create",
        resource_type="knowledge_article",
        resource_id=article.id,
    )
    db.commit()
    db.refresh(article)
    return article


def _validate_entity_exists(db: Session, tenant_id: str, entity_type: str, entity_id: str) -> None:
    if entity_type == "ticket":
        exists = db.scalar(select(Ticket.id).where(Ticket.id == entity_id, Ticket.tenant_id == tenant_id))
    else:
        exists = db.scalar(select(Incident.id).where(Incident.id == entity_id, Incident.tenant_id == tenant_id))
    if exists is None:
        raise HTTPException(status_code=400, detail=f"Invalid {entity_type} reference")


@router.get("/links", response_model=list[EntityKnowledgeLinkOut])
def list_links(
    entity_type: str | None = Query(default=None, pattern=r"^(ticket|incident)$"),
    entity_id: str | None = Query(default=None),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_any_permission("knowledge.read", "knowledge.manage")),
) -> list[EntityKnowledgeLinkOut]:
    query = (
        select(EntityKnowledgeLink)
        .where(EntityKnowledgeLink.tenant_id == current_user.tenant_id)
        .order_by(EntityKnowledgeLink.created_at.desc())
    )
    if entity_type:
        query = query.where(EntityKnowledgeLink.entity_type == entity_type)
    if entity_id:
        query = query.where(EntityKnowledgeLink.entity_id == entity_id)
    return list(db.scalars(query))


@router.post("/links", response_model=EntityKnowledgeLinkOut, status_code=status.HTTP_201_CREATED)
def create_link(
    payload: EntityKnowledgeLinkCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("knowledge.manage")),
) -> EntityKnowledgeLinkOut:
    article = db.scalar(
        select(KnowledgeArticle.id).where(
            KnowledgeArticle.id == payload.article_id,
            KnowledgeArticle.tenant_id == current_user.tenant_id,
        )
    )
    if article is None:
        raise HTTPException(status_code=400, detail="Invalid knowledge article reference")

    _validate_entity_exists(db, current_user.tenant_id, payload.entity_type, payload.entity_id)
    existing = db.scalar(
        select(EntityKnowledgeLink.id).where(
            EntityKnowledgeLink.tenant_id == current_user.tenant_id,
            EntityKnowledgeLink.entity_type == payload.entity_type,
            EntityKnowledgeLink.entity_id == payload.entity_id,
            EntityKnowledgeLink.article_id == payload.article_id,
        )
    )
    if existing is not None:
        raise HTTPException(status_code=409, detail="Knowledge link already exists")

    link = EntityKnowledgeLink(
        tenant_id=current_user.tenant_id,
        entity_type=payload.entity_type,
        entity_id=payload.entity_id,
        article_id=payload.article_id,
        created_by_user_id=current_user.id,
    )
    db.add(link)
    db.flush()
    log_usage_event(
        db,
        tenant_id=current_user.tenant_id,
        actor_user_id=current_user.id,
        event_type="knowledge.link.create",
    )
    log_audit_event(
        db,
        tenant_id=current_user.tenant_id,
        actor_user_id=current_user.id,
        action="knowledge.link_create",
        resource_type="entity_knowledge_link",
        resource_id=link.id,
    )
    db.commit()
    db.refresh(link)
    return link
