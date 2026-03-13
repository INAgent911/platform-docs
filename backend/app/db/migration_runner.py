import uuid
from dataclasses import dataclass
from typing import Callable

from sqlalchemy import inspect, text
from sqlalchemy.engine import Connection, Engine

from app.models import UserRole


ROLE_PERMISSION_SEED: dict[UserRole, set[str]] = {
    UserRole.OWNER: {
        "rbac.manage",
        "schema.manage",
        "incident.manage",
        "change.manage",
        "change.approve",
        "customer.manage",
        "ticket.manage",
        "event.ingest",
    },
    UserRole.ADMIN: {
        "rbac.read",
        "rbac.manage",
        "schema.manage",
        "incident.manage",
        "change.manage",
        "change.approve",
        "customer.manage",
        "ticket.manage",
        "event.ingest",
    },
    UserRole.USER: {"customer.read", "ticket.manage", "event.ingest", "incident.read", "change.read"},
}


@dataclass(frozen=True)
class Migration:
    version: str
    description: str
    apply_fn: Callable[[Connection], None]


def _ensure_migration_table(conn: Connection) -> None:
    conn.execute(
        text(
            """
            CREATE TABLE IF NOT EXISTS schema_migration_versions (
                version VARCHAR(64) PRIMARY KEY,
                description VARCHAR(255) NOT NULL,
                applied_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
    )


def _migration_add_mfa_column(conn: Connection) -> None:
    inspector = inspect(conn)
    if "users" not in inspector.get_table_names():
        return

    existing_columns = {c["name"] for c in inspector.get_columns("users")}
    if "mfa_enabled" in existing_columns:
        return

    if conn.dialect.name == "postgresql":
        conn.execute(text("ALTER TABLE users ADD COLUMN IF NOT EXISTS mfa_enabled BOOLEAN NOT NULL DEFAULT FALSE"))
    else:
        conn.execute(text("ALTER TABLE users ADD COLUMN mfa_enabled BOOLEAN NOT NULL DEFAULT 0"))


def _migration_seed_role_permissions(conn: Connection) -> None:
    inspector = inspect(conn)
    if "role_permissions" not in inspector.get_table_names():
        return

    for role, permissions in ROLE_PERMISSION_SEED.items():
        for permission in permissions:
            exists = conn.execute(
                text(
                    """
                    SELECT 1 FROM role_permissions
                    WHERE role = :role AND permission = :permission
                    LIMIT 1
                    """
                ),
                {"role": role.name, "permission": permission},
            ).fetchone()
            if exists:
                continue
            conn.execute(
                text(
                    """
                    INSERT INTO role_permissions (id, role, permission, description, created_at)
                    VALUES (:id, :role, :permission, :description, CURRENT_TIMESTAMP)
                    """
                ),
                {
                    "id": str(uuid.uuid4()),
                    "role": role.name,
                    "permission": permission,
                    "description": f"Seeded permission {permission}",
                },
            )


def _migration_normalize_role_permissions(conn: Connection) -> None:
    inspector = inspect(conn)
    if "role_permissions" not in inspector.get_table_names():
        return

    if conn.dialect.name == "postgresql":
        legacy_role_query = text(
            """
            SELECT id, permission
            FROM role_permissions
            WHERE role::text = :role
            """
        )
    else:
        legacy_role_query = text(
            """
            SELECT id, permission
            FROM role_permissions
            WHERE role = :role
            """
        )

    role_name_map = {
        UserRole.OWNER.value: UserRole.OWNER.name,
        UserRole.ADMIN.value: UserRole.ADMIN.name,
        UserRole.USER.value: UserRole.USER.name,
    }
    for old_role, new_role in role_name_map.items():
        lowercase_rows = conn.execute(legacy_role_query, {"role": old_role}).fetchall()
        for row in lowercase_rows:
            duplicate = conn.execute(
                text(
                    """
                    SELECT 1
                    FROM role_permissions
                    WHERE role = :role AND permission = :permission
                    LIMIT 1
                    """
                ),
                {"role": new_role, "permission": row.permission},
            ).fetchone()
            if duplicate:
                conn.execute(
                    text(
                        """
                        DELETE FROM role_permissions
                        WHERE id = :id
                        """
                    ),
                    {"id": row.id},
                )
            else:
                conn.execute(
                    text(
                        """
                        UPDATE role_permissions
                        SET role = :new_role
                        WHERE id = :id
                        """
                    ),
                    {"new_role": new_role, "id": row.id},
                )


MIGRATIONS: list[Migration] = [
    Migration(
        version="20260313_001_add_mfa_column",
        description="Add MFA toggle column for users",
        apply_fn=_migration_add_mfa_column,
    ),
    Migration(
        version="20260313_002_seed_role_permissions",
        description="Seed default RBAC role permissions",
        apply_fn=_migration_seed_role_permissions,
    ),
    Migration(
        version="20260313_003_normalize_role_permission_roles",
        description="Normalize RBAC role values to enum names",
        apply_fn=_migration_normalize_role_permissions,
    ),
]


def run_migrations(engine: Engine) -> None:
    with engine.begin() as conn:
        _ensure_migration_table(conn)
        applied_rows = conn.execute(text("SELECT version FROM schema_migration_versions")).fetchall()
        applied = {row[0] for row in applied_rows}

        for migration in MIGRATIONS:
            if migration.version in applied:
                continue
            migration.apply_fn(conn)
            conn.execute(
                text(
                    """
                    INSERT INTO schema_migration_versions (version, description)
                    VALUES (:version, :description)
                    """
                ),
                {"version": migration.version, "description": migration.description},
            )
