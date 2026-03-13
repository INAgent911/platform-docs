from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.deps import require_permission
from app.models import TenantUiSettings, User, WorkspaceView
from app.schemas import UiSettingsOut, UiSettingsUpdate, WorkspaceViewCreate, WorkspaceViewOut
from app.services.audit import log_audit_event
from app.services.usage import log_usage_event

router = APIRouter()


def _get_or_create_ui_settings(db: Session, current_user: User) -> TenantUiSettings:
    settings = db.scalar(
        select(TenantUiSettings).where(TenantUiSettings.tenant_id == current_user.tenant_id)
    )
    if settings is not None:
        return settings
    settings = TenantUiSettings(
        tenant_id=current_user.tenant_id,
        updated_by_user_id=current_user.id,
    )
    db.add(settings)
    db.flush()
    return settings


@router.get("/settings", response_model=UiSettingsOut)
def get_ui_settings(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("ui.manage")),
) -> UiSettingsOut:
    settings = _get_or_create_ui_settings(db, current_user)
    db.commit()
    db.refresh(settings)
    return settings


@router.put("/settings", response_model=UiSettingsOut)
def update_ui_settings(
    payload: UiSettingsUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("ui.manage")),
) -> UiSettingsOut:
    settings = _get_or_create_ui_settings(db, current_user)
    settings.theme_mode = payload.theme_mode
    settings.brand_name = payload.brand_name
    settings.primary_color = payload.primary_color
    settings.secondary_color = payload.secondary_color
    settings.logo_url = payload.logo_url
    settings.updated_by_user_id = current_user.id
    log_usage_event(
        db,
        tenant_id=current_user.tenant_id,
        actor_user_id=current_user.id,
        event_type="ui.settings.update",
        units=1,
    )
    log_audit_event(
        db,
        tenant_id=current_user.tenant_id,
        actor_user_id=current_user.id,
        action="ui.settings_update",
        resource_type="tenant_ui_settings",
        resource_id=settings.id,
        event_data=payload.model_dump(mode="json"),
    )
    db.commit()
    db.refresh(settings)
    return settings


@router.get("/views", response_model=list[WorkspaceViewOut])
def list_workspace_views(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("ui.manage")),
) -> list[WorkspaceViewOut]:
    query = (
        select(WorkspaceView)
        .where(WorkspaceView.tenant_id == current_user.tenant_id)
        .order_by(WorkspaceView.name.asc(), WorkspaceView.version.desc())
    )
    return list(db.scalars(query))


@router.post("/views", response_model=WorkspaceViewOut, status_code=status.HTTP_201_CREATED)
def create_workspace_view(
    payload: WorkspaceViewCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("ui.manage")),
) -> WorkspaceViewOut:
    latest = db.scalar(
        select(WorkspaceView)
        .where(
            WorkspaceView.tenant_id == current_user.tenant_id,
            WorkspaceView.name == payload.name,
        )
        .order_by(WorkspaceView.version.desc())
    )
    next_version = (latest.version + 1) if latest else 1
    view = WorkspaceView(
        tenant_id=current_user.tenant_id,
        name=payload.name,
        role_scope=payload.role_scope,
        layout=payload.layout,
        version=next_version,
        active=payload.activate,
        created_by_user_id=current_user.id,
    )
    if payload.activate:
        db.execute(
            WorkspaceView.__table__.update()
            .where(
                WorkspaceView.tenant_id == current_user.tenant_id,
                WorkspaceView.name == payload.name,
                WorkspaceView.role_scope == payload.role_scope,
            )
            .values(active=False)
        )
    db.add(view)
    db.flush()
    log_usage_event(
        db,
        tenant_id=current_user.tenant_id,
        actor_user_id=current_user.id,
        event_type="ui.workspace_view.create",
        units=1,
    )
    log_audit_event(
        db,
        tenant_id=current_user.tenant_id,
        actor_user_id=current_user.id,
        action="ui.workspace_view_create",
        resource_type="workspace_view",
        resource_id=view.id,
        event_data={"name": view.name, "role_scope": view.role_scope, "version": view.version},
    )
    db.commit()
    db.refresh(view)
    return view


@router.post("/views/{view_id}/activate", response_model=WorkspaceViewOut)
def activate_workspace_view(
    view_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("ui.manage")),
) -> WorkspaceViewOut:
    view = db.scalar(
        select(WorkspaceView).where(
            WorkspaceView.id == view_id,
            WorkspaceView.tenant_id == current_user.tenant_id,
        )
    )
    if view is None:
        raise HTTPException(status_code=404, detail="Workspace view not found")

    db.execute(
        WorkspaceView.__table__.update()
        .where(
            WorkspaceView.tenant_id == current_user.tenant_id,
            WorkspaceView.name == view.name,
            WorkspaceView.role_scope == view.role_scope,
        )
        .values(active=False)
    )
    view.active = True
    log_audit_event(
        db,
        tenant_id=current_user.tenant_id,
        actor_user_id=current_user.id,
        action="ui.workspace_view_activate",
        resource_type="workspace_view",
        resource_id=view.id,
    )
    db.commit()
    db.refresh(view)
    return view
