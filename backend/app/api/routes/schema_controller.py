import yaml
from datetime import datetime, timezone

from sqlalchemy import inspect, select, text
from sqlalchemy.orm import Session
from fastapi import APIRouter, Depends, HTTPException, Query

from app.db.session import get_db
from app.deps import require_permission
from app.models import (
    SchemaFieldMigration,
    SchemaManifest,
    SchemaManifestStatus,
    SchemaMigrationAction,
    SchemaStrategy,
    User,
)
from app.schemas import (
    SchemaApplyOut,
    SchemaFieldMigrationOut,
    SchemaManifestIn,
    SchemaManifestOut,
    SchemaMigrationOperationOut,
    SchemaPlanOut,
    SchemaValidationOut,
    SchemaYamlInput,
)
from app.services.audit import log_audit_event

router = APIRouter()

ENTITY_TABLE_MAP = {"customer": "customer_extensions", "ticket": "ticket_extensions"}


def _validate_manifest(payload: SchemaManifestIn) -> list[str]:
    errors: list[str] = []
    names = [field.name for field in payload.fields]
    if len(names) != len(set(names)):
        errors.append("Field names must be unique")
    if payload.strategy == SchemaStrategy.TYPED and len(payload.fields) > 150:
        errors.append("Typed strategy supports at most 150 custom fields per entity")
    return errors


def _to_sql_type(field_type: str, dialect_name: str) -> str:
    if field_type == "string":
        return "TEXT"
    if field_type == "integer":
        return "INTEGER"
    if field_type == "number":
        return "DOUBLE PRECISION" if dialect_name == "postgresql" else "REAL"
    if field_type == "boolean":
        return "BOOLEAN"
    return "TIMESTAMP"


def _build_plan(db: Session, current_user: User, payload: SchemaManifestIn) -> SchemaPlanOut:
    errors = _validate_manifest(payload)
    latest = db.scalar(
        select(SchemaManifest)
        .where(
            SchemaManifest.tenant_id == current_user.tenant_id,
            SchemaManifest.entity_name == payload.entity_name,
            SchemaManifest.status == SchemaManifestStatus.APPLIED,
        )
        .order_by(SchemaManifest.version.desc())
    )

    current_fields: dict[str, dict] = {}
    if latest and isinstance(latest.manifest, dict):
        for field in latest.manifest.get("fields", []):
            current_fields[field["name"]] = field

    requested_fields = {field.name: field for field in payload.fields}
    warnings: list[str] = []

    operations: list[SchemaMigrationOperationOut] = []
    table_name = ENTITY_TABLE_MAP[payload.entity_name]
    dialect_name = db.get_bind().dialect.name

    if payload.strategy == SchemaStrategy.TYPED:
        inspector = inspect(db.get_bind())
        existing_cols = {col["name"] for col in inspector.get_columns(table_name)}
    else:
        existing_cols = set()

    for field_name, field in requested_fields.items():
        if field_name in current_fields:
            continue
        if payload.strategy == SchemaStrategy.TYPED:
            column_name = f"cf_{field_name}"
            sql_type = _to_sql_type(field.type, dialect_name)
            if column_name in existing_cols:
                warnings.append(f"Column already exists for field '{field_name}', skipping SQL add")
                sql_stmt = None
            else:
                sql_stmt = f"ALTER TABLE {table_name} ADD COLUMN {column_name} {sql_type}"
            operations.append(
                SchemaMigrationOperationOut(
                    action=SchemaMigrationAction.ADD_COLUMN,
                    field_name=field_name,
                    column_name=column_name,
                    data_type=sql_type,
                    table_name=table_name,
                    sql_statement=sql_stmt,
                )
            )
        else:
            operations.append(
                SchemaMigrationOperationOut(
                    action=SchemaMigrationAction.ADD_COLUMN,
                    field_name=field_name,
                    column_name=None,
                    data_type=field.type,
                    table_name=table_name,
                    sql_statement=None,
                )
            )

    removed_fields = set(current_fields.keys()) - set(requested_fields.keys())
    for field_name in sorted(removed_fields):
        operations.append(
            SchemaMigrationOperationOut(
                action=SchemaMigrationAction.DEPRECATE_FIELD,
                field_name=field_name,
                column_name=f"cf_{field_name}" if payload.strategy == SchemaStrategy.TYPED else None,
                data_type=current_fields[field_name].get("type"),
                table_name=table_name,
                sql_statement=None,
            )
        )
        warnings.append(
            f"Field '{field_name}' removed from request. It will be marked deprecated, not dropped."
        )

    return SchemaPlanOut(
        valid=not errors,
        entity_name=payload.entity_name,
        version=payload.version,
        current_version=latest.version if latest else None,
        operations=operations,
        warnings=errors + warnings,
    )


def _parse_yaml_manifest(raw_content: str) -> SchemaManifestIn:
    try:
        data = yaml.safe_load(raw_content)
        return SchemaManifestIn.model_validate(data)
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=400, detail=f"Invalid YAML manifest: {exc}") from exc


def _apply_manifest(
    db: Session,
    current_user: User,
    payload: SchemaManifestIn,
    *,
    dry_run: bool,
) -> SchemaApplyOut:
    plan = _build_plan(db, current_user, payload)
    if not plan.valid:
        raise HTTPException(status_code=400, detail={"validation_errors": plan.warnings})

    manifest = SchemaManifest(
        tenant_id=current_user.tenant_id,
        entity_name=payload.entity_name,
        version=payload.version,
        strategy=payload.strategy,
        status=SchemaManifestStatus.APPLIED,
        manifest=payload.model_dump(mode="json"),
        created_by_user_id=current_user.id,
    )
    db.add(manifest)
    db.flush()

    applied_operations = 0
    for op in plan.operations:
        migration = SchemaFieldMigration(
            tenant_id=current_user.tenant_id,
            manifest_id=manifest.id,
            table_name=op.table_name,
            field_name=op.field_name,
            action=op.action,
            column_name=op.column_name,
            data_type=op.data_type,
            sql_statement=op.sql_statement,
            applied=False,
        )
        if not dry_run and op.sql_statement:
            db.execute(text(op.sql_statement))
            migration.applied = True
            migration.applied_at = datetime.now(timezone.utc)
            applied_operations += 1
        elif op.action == SchemaMigrationAction.DEPRECATE_FIELD:
            migration.applied = True
            migration.applied_at = datetime.now(timezone.utc)
            applied_operations += 1
        db.add(migration)

    log_audit_event(
        db,
        tenant_id=current_user.tenant_id,
        actor_user_id=current_user.id,
        action="schema.apply" if not dry_run else "schema.plan_dry_run",
        resource_type="schema_manifest",
        resource_id=manifest.id,
        event_data={"entity": payload.entity_name, "version": payload.version, "dry_run": dry_run},
    )
    db.commit()

    return SchemaApplyOut(manifest_id=manifest.id, applied_operations=applied_operations, dry_run=dry_run)


@router.post("/validate", response_model=SchemaValidationOut)
def validate_manifest(
    payload: SchemaManifestIn,
    _: User = Depends(require_permission("schema.manage")),
) -> SchemaValidationOut:
    errors = _validate_manifest(payload)
    return SchemaValidationOut(valid=not errors, errors=errors)


@router.post("/validate-yaml", response_model=SchemaValidationOut)
def validate_manifest_yaml(
    payload: SchemaYamlInput,
    _: User = Depends(require_permission("schema.manage")),
) -> SchemaValidationOut:
    manifest = _parse_yaml_manifest(payload.content)
    errors = _validate_manifest(manifest)
    return SchemaValidationOut(valid=not errors, errors=errors)


@router.post("/plan", response_model=SchemaPlanOut)
def plan_manifest(
    payload: SchemaManifestIn,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("schema.manage")),
) -> SchemaPlanOut:
    return _build_plan(db, current_user, payload)


@router.post("/plan-yaml", response_model=SchemaPlanOut)
def plan_manifest_yaml(
    payload: SchemaYamlInput,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("schema.manage")),
) -> SchemaPlanOut:
    manifest = _parse_yaml_manifest(payload.content)
    return _build_plan(db, current_user, manifest)


@router.post("/apply", response_model=SchemaApplyOut)
def apply_manifest(
    payload: SchemaManifestIn,
    dry_run: bool = Query(default=False),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("schema.manage")),
) -> SchemaApplyOut:
    return _apply_manifest(db, current_user, payload, dry_run=dry_run)


@router.post("/apply-yaml", response_model=SchemaApplyOut)
def apply_manifest_yaml(
    payload: SchemaYamlInput,
    dry_run: bool = Query(default=False),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("schema.manage")),
) -> SchemaApplyOut:
    manifest = _parse_yaml_manifest(payload.content)
    return _apply_manifest(db, current_user, manifest, dry_run=dry_run)


@router.get("/manifests", response_model=list[SchemaManifestOut])
def list_manifests(
    entity_name: str | None = Query(default=None),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("schema.manage")),
) -> list[SchemaManifestOut]:
    query = select(SchemaManifest).where(SchemaManifest.tenant_id == current_user.tenant_id).order_by(
        SchemaManifest.created_at.desc()
    )
    if entity_name:
        query = query.where(SchemaManifest.entity_name == entity_name)
    return list(db.scalars(query))


@router.get("/migrations", response_model=list[SchemaFieldMigrationOut])
def list_schema_migrations(
    entity_name: str | None = Query(default=None),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("schema.manage")),
) -> list[SchemaFieldMigrationOut]:
    query = (
        select(SchemaFieldMigration)
        .join(SchemaManifest, SchemaManifest.id == SchemaFieldMigration.manifest_id)
        .where(SchemaFieldMigration.tenant_id == current_user.tenant_id)
        .order_by(SchemaFieldMigration.created_at.desc())
    )
    if entity_name:
        query = query.where(SchemaManifest.entity_name == entity_name)
    return list(db.scalars(query))
