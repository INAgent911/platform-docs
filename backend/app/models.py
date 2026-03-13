import uuid
from datetime import datetime
from enum import StrEnum

from sqlalchemy import (
    JSON,
    Boolean,
    DateTime,
    Enum,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


def _new_id() -> str:
    return str(uuid.uuid4())


class Base(DeclarativeBase):
    pass


class UserRole(StrEnum):
    OWNER = "owner"
    ADMIN = "admin"
    USER = "user"


class Tenant(Base):
    __tablename__ = "tenants"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_new_id)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    slug: Mapped[str] = mapped_column(String(120), unique=True, nullable=False, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    users: Mapped[list["User"]] = relationship(back_populates="tenant", cascade="all, delete-orphan")
    customers: Mapped[list["Customer"]] = relationship(back_populates="tenant", cascade="all, delete-orphan")
    tickets: Mapped[list["Ticket"]] = relationship(back_populates="tenant", cascade="all, delete-orphan")
    alert_events: Mapped[list["AlertEvent"]] = relationship(
        back_populates="tenant", cascade="all, delete-orphan"
    )
    incidents: Mapped[list["Incident"]] = relationship(back_populates="tenant", cascade="all, delete-orphan")
    change_requests: Mapped[list["ChangeRequest"]] = relationship(
        back_populates="tenant", cascade="all, delete-orphan"
    )
    provisioning_jobs: Mapped[list["ProvisioningJob"]] = relationship(
        back_populates="tenant", cascade="all, delete-orphan"
    )
    ui_settings: Mapped["TenantUiSettings"] = relationship(
        back_populates="tenant", cascade="all, delete-orphan", uselist=False
    )
    workspace_views: Mapped[list["WorkspaceView"]] = relationship(
        back_populates="tenant", cascade="all, delete-orphan"
    )
    config_items: Mapped[list["ConfigItem"]] = relationship(back_populates="tenant", cascade="all, delete-orphan")
    service_contracts: Mapped[list["ServiceContract"]] = relationship(
        back_populates="tenant", cascade="all, delete-orphan"
    )
    knowledge_articles: Mapped[list["KnowledgeArticle"]] = relationship(
        back_populates="tenant", cascade="all, delete-orphan"
    )
    usage_events: Mapped[list["UsageEvent"]] = relationship(back_populates="tenant", cascade="all, delete-orphan")
    runbooks: Mapped[list["Runbook"]] = relationship(back_populates="tenant", cascade="all, delete-orphan")
    schema_manifests: Mapped[list["SchemaManifest"]] = relationship(
        back_populates="tenant", cascade="all, delete-orphan"
    )


class User(Base):
    __tablename__ = "users"
    __table_args__ = (UniqueConstraint("tenant_id", "email", name="uq_user_tenant_email"),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_new_id)
    tenant_id: Mapped[str] = mapped_column(ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True)
    email: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    first_name: Mapped[str] = mapped_column(String(120), nullable=False)
    last_name: Mapped[str] = mapped_column(String(120), nullable=False)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[UserRole] = mapped_column(Enum(UserRole), nullable=False, default=UserRole.USER)
    is_active: Mapped[bool] = mapped_column(default=True, nullable=False)
    mfa_enabled: Mapped[bool] = mapped_column(Boolean(), default=False, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    tenant: Mapped[Tenant] = relationship(back_populates="users")


class CustomerStatus(StrEnum):
    ACTIVE = "active"
    PROSPECT = "prospect"
    INACTIVE = "inactive"


class Customer(Base):
    __tablename__ = "customers"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_new_id)
    tenant_id: Mapped[str] = mapped_column(ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    status: Mapped[CustomerStatus] = mapped_column(
        Enum(CustomerStatus), nullable=False, default=CustomerStatus.ACTIVE
    )
    notes: Mapped[str | None] = mapped_column(Text(), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    tenant: Mapped[Tenant] = relationship(back_populates="customers")
    tickets: Mapped[list["Ticket"]] = relationship(back_populates="customer")


class TicketStatus(StrEnum):
    NEW = "new"
    IN_PROGRESS = "in_progress"
    DONE = "done"


class TicketPriority(StrEnum):
    P1 = "p1"
    P2 = "p2"
    P3 = "p3"
    P4 = "p4"


class Ticket(Base):
    __tablename__ = "tickets"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_new_id)
    tenant_id: Mapped[str] = mapped_column(ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True)
    customer_id: Mapped[str | None] = mapped_column(ForeignKey("customers.id"), nullable=True, index=True)
    config_item_id: Mapped[str | None] = mapped_column(String(36), nullable=True, index=True)
    contract_id: Mapped[str | None] = mapped_column(String(36), nullable=True, index=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text(), nullable=True)
    status: Mapped[TicketStatus] = mapped_column(Enum(TicketStatus), nullable=False, default=TicketStatus.NEW)
    priority: Mapped[TicketPriority] = mapped_column(
        Enum(TicketPriority), nullable=False, default=TicketPriority.P3
    )
    first_responded_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    response_due_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True, index=True)
    resolved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    resolve_due_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True, index=True)
    escalated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    tenant: Mapped[Tenant] = relationship(back_populates="tickets")
    customer: Mapped[Customer | None] = relationship(back_populates="tickets")
    incidents: Mapped[list["Incident"]] = relationship(back_populates="ticket")
    change_requests: Mapped[list["ChangeRequest"]] = relationship(back_populates="ticket")


class AlertEvent(Base):
    __tablename__ = "alert_events"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_new_id)
    tenant_id: Mapped[str] = mapped_column(ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True)
    event_type: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    source: Mapped[str] = mapped_column(String(255), nullable=False)
    severity: Mapped[str | None] = mapped_column(String(50), nullable=True, index=True)
    subject: Mapped[str | None] = mapped_column(String(255), nullable=True)
    external_event_id: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    payload: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    occurred_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    received_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    tenant: Mapped[Tenant] = relationship(back_populates="alert_events")


class AuditEvent(Base):
    __tablename__ = "audit_events"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_new_id)
    tenant_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True)
    actor_user_id: Mapped[str | None] = mapped_column(String(36), nullable=True, index=True)
    action: Mapped[str] = mapped_column(String(120), nullable=False)
    resource_type: Mapped[str] = mapped_column(String(120), nullable=False)
    resource_id: Mapped[str | None] = mapped_column(String(120), nullable=True)
    event_data: Mapped[dict] = mapped_column("metadata", JSON, nullable=False, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)


class RolePermission(Base):
    __tablename__ = "role_permissions"
    __table_args__ = (UniqueConstraint("role", "permission", name="uq_role_permission"),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_new_id)
    role: Mapped[UserRole] = mapped_column(Enum(UserRole), nullable=False, index=True)
    permission: Mapped[str] = mapped_column(String(120), nullable=False)
    description: Mapped[str] = mapped_column(String(255), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)


class SchemaManifestStatus(StrEnum):
    DRAFT = "draft"
    APPLIED = "applied"


class SchemaStrategy(StrEnum):
    JSONB = "jsonb"
    TYPED = "typed"


class SchemaManifest(Base):
    __tablename__ = "schema_manifests"
    __table_args__ = (UniqueConstraint("tenant_id", "entity_name", "version", name="uq_schema_manifest"),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_new_id)
    tenant_id: Mapped[str] = mapped_column(ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True)
    entity_name: Mapped[str] = mapped_column(String(120), nullable=False, index=True)
    version: Mapped[int] = mapped_column(Integer(), nullable=False)
    strategy: Mapped[SchemaStrategy] = mapped_column(
        Enum(SchemaStrategy), nullable=False, default=SchemaStrategy.TYPED
    )
    status: Mapped[SchemaManifestStatus] = mapped_column(
        Enum(SchemaManifestStatus), nullable=False, default=SchemaManifestStatus.APPLIED
    )
    manifest: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    created_by_user_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    tenant: Mapped[Tenant] = relationship(back_populates="schema_manifests")
    migrations: Mapped[list["SchemaFieldMigration"]] = relationship(
        back_populates="manifest_ref", cascade="all, delete-orphan"
    )


class SchemaMigrationAction(StrEnum):
    ADD_COLUMN = "add_column"
    DEPRECATE_FIELD = "deprecate_field"


class SchemaFieldMigration(Base):
    __tablename__ = "schema_field_migrations"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_new_id)
    tenant_id: Mapped[str] = mapped_column(ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True)
    manifest_id: Mapped[str] = mapped_column(
        ForeignKey("schema_manifests.id", ondelete="CASCADE"), nullable=False, index=True
    )
    table_name: Mapped[str] = mapped_column(String(120), nullable=False)
    field_name: Mapped[str] = mapped_column(String(120), nullable=False)
    action: Mapped[SchemaMigrationAction] = mapped_column(Enum(SchemaMigrationAction), nullable=False)
    column_name: Mapped[str | None] = mapped_column(String(120), nullable=True)
    data_type: Mapped[str | None] = mapped_column(String(50), nullable=True)
    sql_statement: Mapped[str | None] = mapped_column(Text(), nullable=True)
    applied: Mapped[bool] = mapped_column(Boolean(), nullable=False, default=False)
    applied_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    manifest_ref: Mapped[SchemaManifest] = relationship(back_populates="migrations")


class CustomerExtension(Base):
    __tablename__ = "customer_extensions"
    __table_args__ = (UniqueConstraint("tenant_id", "customer_id", name="uq_customer_ext"),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_new_id)
    tenant_id: Mapped[str] = mapped_column(ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True)
    customer_id: Mapped[str] = mapped_column(ForeignKey("customers.id", ondelete="CASCADE"), nullable=False, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)


class TicketExtension(Base):
    __tablename__ = "ticket_extensions"
    __table_args__ = (UniqueConstraint("tenant_id", "ticket_id", name="uq_ticket_ext"),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_new_id)
    tenant_id: Mapped[str] = mapped_column(ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True)
    ticket_id: Mapped[str] = mapped_column(ForeignKey("tickets.id", ondelete="CASCADE"), nullable=False, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)


class IncidentSeverity(StrEnum):
    SEV1 = "sev1"
    SEV2 = "sev2"
    SEV3 = "sev3"
    SEV4 = "sev4"


class IncidentStatus(StrEnum):
    OPEN = "open"
    INVESTIGATING = "investigating"
    MITIGATED = "mitigated"
    RESOLVED = "resolved"
    CLOSED = "closed"


class Incident(Base):
    __tablename__ = "incidents"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_new_id)
    tenant_id: Mapped[str] = mapped_column(ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True)
    ticket_id: Mapped[str | None] = mapped_column(ForeignKey("tickets.id"), nullable=True, index=True)
    customer_id: Mapped[str | None] = mapped_column(ForeignKey("customers.id"), nullable=True, index=True)
    config_item_id: Mapped[str | None] = mapped_column(String(36), nullable=True, index=True)
    contract_id: Mapped[str | None] = mapped_column(String(36), nullable=True, index=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    summary: Mapped[str | None] = mapped_column(Text(), nullable=True)
    status: Mapped[IncidentStatus] = mapped_column(Enum(IncidentStatus), nullable=False, default=IncidentStatus.OPEN)
    severity: Mapped[IncidentSeverity] = mapped_column(
        Enum(IncidentSeverity), nullable=False, default=IncidentSeverity.SEV3
    )
    is_major: Mapped[bool] = mapped_column(Boolean(), nullable=False, default=False)
    assigned_user_id: Mapped[str | None] = mapped_column(String(36), nullable=True, index=True)
    communication_interval_minutes: Mapped[int] = mapped_column(Integer(), nullable=False, default=60)
    last_communication_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    next_communication_due_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True, index=True
    )
    resolved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_by_user_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    tenant: Mapped[Tenant] = relationship(back_populates="incidents")
    ticket: Mapped[Ticket | None] = relationship(back_populates="incidents")
    change_requests: Mapped[list["ChangeRequest"]] = relationship(back_populates="incident")


class ChangeType(StrEnum):
    STANDARD = "standard"
    NORMAL = "normal"
    EMERGENCY = "emergency"


class ChangeStatus(StrEnum):
    DRAFT = "draft"
    PENDING_APPROVAL = "pending_approval"
    APPROVED = "approved"
    REJECTED = "rejected"
    SCHEDULED = "scheduled"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    ROLLED_BACK = "rolled_back"
    CANCELLED = "cancelled"


class Runbook(Base):
    __tablename__ = "runbooks"
    __table_args__ = (UniqueConstraint("tenant_id", "name", name="uq_runbook_name"),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_new_id)
    tenant_id: Mapped[str] = mapped_column(ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    description: Mapped[str | None] = mapped_column(Text(), nullable=True)
    enabled: Mapped[bool] = mapped_column(Boolean(), nullable=False, default=True)
    auto_approve_low_risk: Mapped[bool] = mapped_column(Boolean(), nullable=False, default=False)
    min_risk_score: Mapped[int] = mapped_column(Integer(), nullable=False, default=1)
    max_risk_score: Mapped[int] = mapped_column(Integer(), nullable=False, default=3)
    execution_template: Mapped[str | None] = mapped_column(Text(), nullable=True)
    created_by_user_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    tenant: Mapped[Tenant] = relationship(back_populates="runbooks")
    change_requests: Mapped[list["ChangeRequest"]] = relationship(back_populates="runbook")


class ChangeRequest(Base):
    __tablename__ = "change_requests"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_new_id)
    tenant_id: Mapped[str] = mapped_column(ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True)
    incident_id: Mapped[str | None] = mapped_column(ForeignKey("incidents.id"), nullable=True, index=True)
    ticket_id: Mapped[str | None] = mapped_column(ForeignKey("tickets.id"), nullable=True, index=True)
    config_item_id: Mapped[str | None] = mapped_column(String(36), nullable=True, index=True)
    contract_id: Mapped[str | None] = mapped_column(String(36), nullable=True, index=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text(), nullable=True)
    change_type: Mapped[ChangeType] = mapped_column(Enum(ChangeType), nullable=False, default=ChangeType.NORMAL)
    status: Mapped[ChangeStatus] = mapped_column(Enum(ChangeStatus), nullable=False, default=ChangeStatus.DRAFT)
    risk_score: Mapped[int] = mapped_column(Integer(), nullable=False, default=5)
    runbook_id: Mapped[str | None] = mapped_column(ForeignKey("runbooks.id"), nullable=True, index=True)
    automated_approval: Mapped[bool] = mapped_column(Boolean(), nullable=False, default=False)
    execution_status: Mapped[str] = mapped_column(String(40), nullable=False, default="not_executed")
    execution_output: Mapped[str | None] = mapped_column(Text(), nullable=True)
    executed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    rollback_plan: Mapped[str | None] = mapped_column(Text(), nullable=True)
    scheduled_start_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    scheduled_end_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    requested_by_user_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True)
    approved_by_user_id: Mapped[str | None] = mapped_column(String(36), nullable=True, index=True)
    approval_notes: Mapped[str | None] = mapped_column(Text(), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    tenant: Mapped[Tenant] = relationship(back_populates="change_requests")
    incident: Mapped[Incident | None] = relationship(back_populates="change_requests")
    ticket: Mapped[Ticket | None] = relationship(back_populates="change_requests")
    runbook: Mapped[Runbook | None] = relationship(back_populates="change_requests")


class ProvisioningStatus(StrEnum):
    QUEUED = "queued"
    RUNNING = "running"
    SUCCEEDED = "succeeded"
    FAILED = "failed"


class ProvisioningJob(Base):
    __tablename__ = "provisioning_jobs"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_new_id)
    tenant_id: Mapped[str] = mapped_column(ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True)
    requested_by_user_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True)
    package_name: Mapped[str] = mapped_column(String(120), nullable=False, default="core")
    allowed_first_user_email: Mapped[str | None] = mapped_column(String(255), nullable=True)
    status: Mapped[ProvisioningStatus] = mapped_column(
        Enum(ProvisioningStatus), nullable=False, default=ProvisioningStatus.QUEUED
    )
    steps: Mapped[list] = mapped_column(JSON, nullable=False, default=list)
    error_message: Mapped[str | None] = mapped_column(Text(), nullable=True)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    tenant: Mapped[Tenant] = relationship(back_populates="provisioning_jobs")


class ThemeMode(StrEnum):
    LIGHT = "light"
    DARK = "dark"


class TenantUiSettings(Base):
    __tablename__ = "tenant_ui_settings"
    __table_args__ = (UniqueConstraint("tenant_id", name="uq_tenant_ui_settings"),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_new_id)
    tenant_id: Mapped[str] = mapped_column(ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True)
    theme_mode: Mapped[ThemeMode] = mapped_column(Enum(ThemeMode), nullable=False, default=ThemeMode.LIGHT)
    brand_name: Mapped[str | None] = mapped_column(String(120), nullable=True)
    primary_color: Mapped[str] = mapped_column(String(20), nullable=False, default="#0b5fff")
    secondary_color: Mapped[str] = mapped_column(String(20), nullable=False, default="#00a389")
    logo_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    updated_by_user_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    tenant: Mapped[Tenant] = relationship(back_populates="ui_settings")


class WorkspaceView(Base):
    __tablename__ = "workspace_views"
    __table_args__ = (UniqueConstraint("tenant_id", "name", "version", name="uq_workspace_view"),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_new_id)
    tenant_id: Mapped[str] = mapped_column(ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    role_scope: Mapped[str] = mapped_column(String(40), nullable=False, default="user")
    layout: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    version: Mapped[int] = mapped_column(Integer(), nullable=False, default=1)
    active: Mapped[bool] = mapped_column(Boolean(), nullable=False, default=True)
    created_by_user_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    tenant: Mapped[Tenant] = relationship(back_populates="workspace_views")


class ConfigItem(Base):
    __tablename__ = "config_items"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_new_id)
    tenant_id: Mapped[str] = mapped_column(ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    item_type: Mapped[str] = mapped_column(String(80), nullable=False)
    environment: Mapped[str | None] = mapped_column(String(80), nullable=True)
    criticality: Mapped[str | None] = mapped_column(String(40), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    tenant: Mapped[Tenant] = relationship(back_populates="config_items")


class ServiceContract(Base):
    __tablename__ = "service_contracts"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_new_id)
    tenant_id: Mapped[str] = mapped_column(ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True)
    contract_code: Mapped[str] = mapped_column(String(80), nullable=False)
    customer_name: Mapped[str] = mapped_column(String(255), nullable=False)
    sla_tier: Mapped[str] = mapped_column(String(80), nullable=False, default="standard")
    starts_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    ends_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    tenant: Mapped[Tenant] = relationship(back_populates="service_contracts")


class KnowledgeArticle(Base):
    __tablename__ = "knowledge_articles"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_new_id)
    tenant_id: Mapped[str] = mapped_column(ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    body: Mapped[str] = mapped_column(Text(), nullable=False)
    tags: Mapped[list] = mapped_column(JSON, nullable=False, default=list)
    known_error_code: Mapped[str | None] = mapped_column(String(80), nullable=True, index=True)
    created_by_user_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    tenant: Mapped[Tenant] = relationship(back_populates="knowledge_articles")


class EntityKnowledgeLink(Base):
    __tablename__ = "entity_knowledge_links"
    __table_args__ = (
        UniqueConstraint("tenant_id", "entity_type", "entity_id", "article_id", name="uq_entity_knowledge_link"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_new_id)
    tenant_id: Mapped[str] = mapped_column(ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True)
    entity_type: Mapped[str] = mapped_column(String(40), nullable=False, index=True)
    entity_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True)
    article_id: Mapped[str] = mapped_column(
        ForeignKey("knowledge_articles.id", ondelete="CASCADE"), nullable=False, index=True
    )
    created_by_user_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)


class UsageEvent(Base):
    __tablename__ = "usage_events"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_new_id)
    tenant_id: Mapped[str] = mapped_column(ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True)
    actor_user_id: Mapped[str | None] = mapped_column(String(36), nullable=True, index=True)
    event_type: Mapped[str] = mapped_column(String(80), nullable=False, index=True)
    units: Mapped[int] = mapped_column(Integer(), nullable=False, default=1)
    cost_estimate_usd_micros: Mapped[int] = mapped_column(Integer(), nullable=False, default=0)
    event_metadata: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    tenant: Mapped[Tenant] = relationship(back_populates="usage_events")
