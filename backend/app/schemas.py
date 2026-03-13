from datetime import datetime

from pydantic import BaseModel, EmailStr, Field

from app.models import (
    ChangeStatus,
    ChangeType,
    CustomerStatus,
    IncidentSeverity,
    IncidentStatus,
    ProvisioningStatus,
    SchemaMigrationAction,
    SchemaManifestStatus,
    SchemaStrategy,
    TicketPriority,
    TicketStatus,
    ThemeMode,
    UserRole,
)


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class OwnerRegistration(BaseModel):
    tenant_name: str = Field(min_length=2, max_length=255)
    tenant_slug: str = Field(min_length=2, max_length=120, pattern=r"^[a-z0-9-]+$")
    email: EmailStr
    password: str = Field(min_length=10, max_length=128)
    first_name: str = Field(min_length=1, max_length=120)
    last_name: str = Field(min_length=1, max_length=120)


class LoginRequest(BaseModel):
    tenant_slug: str
    email: EmailStr
    password: str


class UserOut(BaseModel):
    id: str
    tenant_id: str
    email: EmailStr
    first_name: str
    last_name: str
    role: UserRole
    is_active: bool
    mfa_enabled: bool

    model_config = {"from_attributes": True}


class UserCreate(BaseModel):
    email: EmailStr
    first_name: str = Field(min_length=1, max_length=120)
    last_name: str = Field(min_length=1, max_length=120)
    password: str = Field(min_length=10, max_length=128)
    role: UserRole = UserRole.USER
    mfa_enabled: bool = False


class UserRoleUpdate(BaseModel):
    role: UserRole


class UserActiveUpdate(BaseModel):
    is_active: bool


class TenantOut(BaseModel):
    id: str
    name: str
    slug: str
    created_at: datetime

    model_config = {"from_attributes": True}


class RolePermissionOut(BaseModel):
    role: UserRole
    permission: str
    description: str

    model_config = {"from_attributes": True}


class CustomerCreate(BaseModel):
    name: str = Field(min_length=2, max_length=255)
    status: CustomerStatus = CustomerStatus.ACTIVE
    notes: str | None = None


class CustomerUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=2, max_length=255)
    status: CustomerStatus | None = None
    notes: str | None = None


class CustomerOut(BaseModel):
    id: str
    tenant_id: str
    name: str
    status: CustomerStatus
    notes: str | None
    created_at: datetime

    model_config = {"from_attributes": True}


class TicketCreate(BaseModel):
    title: str = Field(min_length=3, max_length=255)
    description: str | None = None
    customer_id: str | None = None
    config_item_id: str | None = None
    contract_id: str | None = None
    priority: TicketPriority = TicketPriority.P3


class TicketUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=3, max_length=255)
    description: str | None = None
    status: TicketStatus | None = None
    priority: TicketPriority | None = None
    customer_id: str | None = None
    config_item_id: str | None = None
    contract_id: str | None = None


class TicketOut(BaseModel):
    id: str
    tenant_id: str
    customer_id: str | None
    config_item_id: str | None
    contract_id: str | None
    title: str
    description: str | None
    status: TicketStatus
    priority: TicketPriority
    first_responded_at: datetime | None
    response_due_at: datetime | None
    resolved_at: datetime | None
    resolve_due_at: datetime | None
    escalated_at: datetime | None
    created_at: datetime

    model_config = {"from_attributes": True}


class TicketSlaOut(BaseModel):
    ticket_id: str
    response_due_at: datetime | None
    resolve_due_at: datetime | None
    first_responded_at: datetime | None
    resolved_at: datetime | None
    escalated_at: datetime | None
    response_breached: bool
    resolution_breached: bool
    is_escalated: bool


class CloudEventIn(BaseModel):
    specversion: str = "1.0"
    type: str
    source: str
    id: str
    time: datetime
    subject: str | None = None
    datacontenttype: str | None = "application/json"
    data: dict = Field(default_factory=dict)


class AlertEventOut(BaseModel):
    id: str
    event_type: str
    source: str
    severity: str | None
    subject: str | None
    external_event_id: str
    occurred_at: datetime
    received_at: datetime

    model_config = {"from_attributes": True}


class IncidentCreate(BaseModel):
    title: str = Field(min_length=3, max_length=255)
    summary: str | None = None
    severity: IncidentSeverity = IncidentSeverity.SEV3
    status: IncidentStatus = IncidentStatus.OPEN
    is_major: bool = False
    ticket_id: str | None = None
    customer_id: str | None = None
    config_item_id: str | None = None
    contract_id: str | None = None
    assigned_user_id: str | None = None
    communication_interval_minutes: int | None = Field(default=None, ge=5, le=24 * 60)


class IncidentUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=3, max_length=255)
    summary: str | None = None
    severity: IncidentSeverity | None = None
    status: IncidentStatus | None = None
    is_major: bool | None = None
    config_item_id: str | None = None
    contract_id: str | None = None
    assigned_user_id: str | None = None
    communication_interval_minutes: int | None = Field(default=None, ge=5, le=24 * 60)


class IncidentCommunicationUpdate(BaseModel):
    note: str | None = Field(default=None, max_length=2000)


class IncidentOut(BaseModel):
    id: str
    tenant_id: str
    ticket_id: str | None
    customer_id: str | None
    config_item_id: str | None
    contract_id: str | None
    title: str
    summary: str | None
    status: IncidentStatus
    severity: IncidentSeverity
    is_major: bool
    assigned_user_id: str | None
    communication_interval_minutes: int
    last_communication_at: datetime | None
    next_communication_due_at: datetime | None
    resolved_at: datetime | None
    created_by_user_id: str
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class RunbookCreate(BaseModel):
    name: str = Field(min_length=2, max_length=120)
    description: str | None = None
    auto_approve_low_risk: bool = False
    min_risk_score: int = Field(default=1, ge=1, le=10)
    max_risk_score: int = Field(default=3, ge=1, le=10)
    execution_template: str | None = None


class RunbookOut(BaseModel):
    id: str
    tenant_id: str
    name: str
    description: str | None
    enabled: bool
    auto_approve_low_risk: bool
    min_risk_score: int
    max_risk_score: int
    execution_template: str | None
    created_by_user_id: str
    created_at: datetime

    model_config = {"from_attributes": True}


class ChangeRequestCreate(BaseModel):
    title: str = Field(min_length=3, max_length=255)
    description: str | None = None
    change_type: ChangeType = ChangeType.NORMAL
    risk_score: int = Field(default=5, ge=1, le=10)
    runbook_id: str | None = None
    config_item_id: str | None = None
    contract_id: str | None = None
    rollback_plan: str | None = None
    incident_id: str | None = None
    ticket_id: str | None = None
    scheduled_start_at: datetime | None = None
    scheduled_end_at: datetime | None = None


class ChangeRequestUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=3, max_length=255)
    description: str | None = None
    change_type: ChangeType | None = None
    risk_score: int | None = Field(default=None, ge=1, le=10)
    runbook_id: str | None = None
    config_item_id: str | None = None
    contract_id: str | None = None
    rollback_plan: str | None = None
    incident_id: str | None = None
    ticket_id: str | None = None
    scheduled_start_at: datetime | None = None
    scheduled_end_at: datetime | None = None
    status: ChangeStatus | None = None


class ChangeApprovalRequest(BaseModel):
    approved: bool
    approval_notes: str | None = None


class ChangeExecutionUpdate(BaseModel):
    rolled_back: bool = False


class ChangeRequestOut(BaseModel):
    id: str
    tenant_id: str
    incident_id: str | None
    ticket_id: str | None
    config_item_id: str | None
    contract_id: str | None
    title: str
    description: str | None
    change_type: ChangeType
    status: ChangeStatus
    risk_score: int
    runbook_id: str | None
    automated_approval: bool
    execution_status: str
    execution_output: str | None
    executed_at: datetime | None
    rollback_plan: str | None
    scheduled_start_at: datetime | None
    scheduled_end_at: datetime | None
    requested_by_user_id: str
    approved_by_user_id: str | None
    approval_notes: str | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class ProvisioningJobCreate(BaseModel):
    package_name: str = Field(default="core", min_length=1, max_length=120)
    allowed_first_user_email: EmailStr | None = None


class ProvisioningJobRetry(BaseModel):
    reset_error: bool = True


class ProvisioningJobOut(BaseModel):
    id: str
    tenant_id: str
    requested_by_user_id: str
    package_name: str
    allowed_first_user_email: str | None
    status: ProvisioningStatus
    steps: list
    error_message: str | None
    started_at: datetime | None
    completed_at: datetime | None
    created_at: datetime

    model_config = {"from_attributes": True}


class UiSettingsUpdate(BaseModel):
    theme_mode: ThemeMode
    brand_name: str | None = Field(default=None, max_length=120)
    primary_color: str = Field(default="#0b5fff", pattern=r"^#[0-9a-fA-F]{6}$")
    secondary_color: str = Field(default="#00a389", pattern=r"^#[0-9a-fA-F]{6}$")
    logo_url: str | None = Field(default=None, max_length=500)


class UiSettingsOut(BaseModel):
    id: str
    tenant_id: str
    theme_mode: ThemeMode
    brand_name: str | None
    primary_color: str
    secondary_color: str
    logo_url: str | None
    updated_by_user_id: str
    updated_at: datetime

    model_config = {"from_attributes": True}


class WorkspaceViewCreate(BaseModel):
    name: str = Field(min_length=2, max_length=120)
    role_scope: str = Field(pattern=r"^(owner|admin|user)$")
    layout: dict = Field(default_factory=dict)
    activate: bool = True


class WorkspaceViewOut(BaseModel):
    id: str
    tenant_id: str
    name: str
    role_scope: str
    layout: dict
    version: int
    active: bool
    created_by_user_id: str
    created_at: datetime

    model_config = {"from_attributes": True}


class ConfigItemCreate(BaseModel):
    name: str = Field(min_length=2, max_length=120)
    item_type: str = Field(min_length=2, max_length=80)
    environment: str | None = Field(default=None, max_length=80)
    criticality: str | None = Field(default=None, max_length=40)


class ConfigItemOut(BaseModel):
    id: str
    tenant_id: str
    name: str
    item_type: str
    environment: str | None
    criticality: str | None
    created_at: datetime

    model_config = {"from_attributes": True}


class ServiceContractCreate(BaseModel):
    contract_code: str = Field(min_length=2, max_length=80)
    customer_name: str = Field(min_length=2, max_length=255)
    sla_tier: str = Field(min_length=2, max_length=80)
    starts_at: datetime | None = None
    ends_at: datetime | None = None


class ServiceContractOut(BaseModel):
    id: str
    tenant_id: str
    contract_code: str
    customer_name: str
    sla_tier: str
    starts_at: datetime | None
    ends_at: datetime | None
    created_at: datetime

    model_config = {"from_attributes": True}


class KnowledgeArticleCreate(BaseModel):
    title: str = Field(min_length=3, max_length=255)
    body: str = Field(min_length=10)
    tags: list[str] = Field(default_factory=list)
    known_error_code: str | None = Field(default=None, max_length=80)


class KnowledgeArticleOut(BaseModel):
    id: str
    tenant_id: str
    title: str
    body: str
    tags: list
    known_error_code: str | None
    created_by_user_id: str
    created_at: datetime

    model_config = {"from_attributes": True}


class EntityKnowledgeLinkCreate(BaseModel):
    entity_type: str = Field(pattern=r"^(ticket|incident)$")
    entity_id: str = Field(min_length=36, max_length=36)
    article_id: str = Field(min_length=36, max_length=36)


class EntityKnowledgeLinkOut(BaseModel):
    id: str
    tenant_id: str
    entity_type: str
    entity_id: str
    article_id: str
    created_by_user_id: str
    created_at: datetime

    model_config = {"from_attributes": True}


class AiCopilotRequest(BaseModel):
    query: str = Field(min_length=3, max_length=2000)
    include_closed: bool = False
    max_results: int = Field(default=5, ge=1, le=20)


class AiCopilotRecommendation(BaseModel):
    title: str
    confidence: float = Field(ge=0.0, le=1.0)
    rationale: str


class AiCopilotResultOut(BaseModel):
    root_cause_category: str
    suggested_runbooks: list[str]
    recommended_articles: list[KnowledgeArticleOut]
    similar_tickets: list[TicketOut]
    recommendations: list[AiCopilotRecommendation]


class UsageEventOut(BaseModel):
    id: str
    tenant_id: str
    actor_user_id: str | None
    event_type: str
    units: int
    cost_estimate_usd_micros: int
    event_metadata: dict
    created_at: datetime

    model_config = {"from_attributes": True}


class WorkflowTemplateOut(BaseModel):
    id: str
    name: str
    description: str


class WorkflowRunOut(BaseModel):
    template_id: str
    executed_at: datetime
    summary: str
    affected_records: int


class OpsReportOut(BaseModel):
    tickets_open: int
    tickets_overdue: int
    incidents_open: int
    incidents_major_open: int
    changes_pending_approval: int
    changes_failed_or_rollback: int
    mttr_minutes: int | None


class UsageReportOut(BaseModel):
    total_events: int
    total_units: int
    total_estimated_cost_usd: float
    by_event_type: dict[str, int]


class SchemaFieldDefinitionIn(BaseModel):
    name: str = Field(min_length=1, max_length=64, pattern=r"^[a-z][a-z0-9_]*$")
    type: str = Field(pattern=r"^(string|integer|number|boolean|date)$")
    required: bool = False
    description: str | None = None
    default: str | int | float | bool | None = None
    vectorize: bool = False


class SchemaManifestIn(BaseModel):
    entity_name: str = Field(pattern=r"^(customer|ticket)$")
    version: int = Field(ge=1, le=1000)
    strategy: SchemaStrategy = SchemaStrategy.TYPED
    fields: list[SchemaFieldDefinitionIn]


class SchemaYamlInput(BaseModel):
    content: str = Field(min_length=1)


class SchemaValidationOut(BaseModel):
    valid: bool
    errors: list[str]


class SchemaMigrationOperationOut(BaseModel):
    action: SchemaMigrationAction
    field_name: str
    column_name: str | None
    data_type: str | None
    table_name: str
    sql_statement: str | None


class SchemaPlanOut(BaseModel):
    valid: bool
    entity_name: str
    version: int
    current_version: int | None
    operations: list[SchemaMigrationOperationOut]
    warnings: list[str]


class SchemaApplyOut(BaseModel):
    manifest_id: str
    applied_operations: int
    dry_run: bool


class SchemaManifestOut(BaseModel):
    id: str
    tenant_id: str
    entity_name: str
    version: int
    strategy: SchemaStrategy
    status: SchemaManifestStatus
    manifest: dict
    created_by_user_id: str
    created_at: datetime

    model_config = {"from_attributes": True}


class SchemaFieldMigrationOut(BaseModel):
    id: str
    tenant_id: str
    manifest_id: str
    table_name: str
    field_name: str
    action: SchemaMigrationAction
    column_name: str | None
    data_type: str | None
    sql_statement: str | None
    applied: bool
    applied_at: datetime | None
    created_at: datetime

    model_config = {"from_attributes": True}
