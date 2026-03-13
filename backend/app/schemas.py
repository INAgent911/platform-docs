from datetime import datetime

from pydantic import BaseModel, EmailStr, Field

from app.models import (
    ChangeStatus,
    ChangeType,
    CustomerStatus,
    IncidentSeverity,
    IncidentStatus,
    SchemaMigrationAction,
    SchemaManifestStatus,
    SchemaStrategy,
    TicketPriority,
    TicketStatus,
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
    priority: TicketPriority = TicketPriority.P3


class TicketUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=3, max_length=255)
    description: str | None = None
    status: TicketStatus | None = None
    priority: TicketPriority | None = None
    customer_id: str | None = None


class TicketOut(BaseModel):
    id: str
    tenant_id: str
    customer_id: str | None
    title: str
    description: str | None
    status: TicketStatus
    priority: TicketPriority
    created_at: datetime

    model_config = {"from_attributes": True}


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
    assigned_user_id: str | None = None
    communication_interval_minutes: int = Field(default=60, ge=5, le=240)


class IncidentUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=3, max_length=255)
    summary: str | None = None
    severity: IncidentSeverity | None = None
    status: IncidentStatus | None = None
    is_major: bool | None = None
    assigned_user_id: str | None = None
    communication_interval_minutes: int | None = Field(default=None, ge=5, le=240)


class IncidentOut(BaseModel):
    id: str
    tenant_id: str
    ticket_id: str | None
    customer_id: str | None
    title: str
    summary: str | None
    status: IncidentStatus
    severity: IncidentSeverity
    is_major: bool
    assigned_user_id: str | None
    communication_interval_minutes: int
    created_by_user_id: str
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class ChangeRequestCreate(BaseModel):
    title: str = Field(min_length=3, max_length=255)
    description: str | None = None
    change_type: ChangeType = ChangeType.NORMAL
    risk_score: int = Field(default=5, ge=1, le=10)
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
    title: str
    description: str | None
    change_type: ChangeType
    status: ChangeStatus
    risk_score: int
    rollback_plan: str | None
    scheduled_start_at: datetime | None
    scheduled_end_at: datetime | None
    requested_by_user_id: str
    approved_by_user_id: str | None
    approval_notes: str | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


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
