# 00. Requirements Baseline (From Provided Ideas)

This file captures the interpreted baseline from your Confluence export so architecture decisions remain traceable.

## Captured Vision Themes

- AI-native MSP SaaS platform.
- High customization for tables, fields, and UI views.
- Multi-tenant model with secure sharing/community patterns.
- Strong security/compliance, auditability, and versioning.
- Workflow automation connected to Microsoft ecosystem.
- Search and copilot experiences (keyword + semantic).
- Reporting, benchmarking, and consumption-based billing.

## Captured Design Order

1. Environment
2. Database
3. Users
4. Provisioning
5. Views Customization

## Captured Technical Constraints

- Python backend, React frontend, Material UI.
- Docker local runtime.
- Azure deployment target.
- Postgres + blob storage.
- YAML-defined schema with update lifecycle.
- Record-level permissions to constrain AI access.
- 2FA-capable user system with first-user owner pattern.

## Captured UI Requirements

- Left nav (3-level, collapsible).
- Top bar with logo/search/create/notifications/AI/help/community/user.
- Main content area + breadcrumbs.
- Theme/branding controls with dark/light modes.
- Data-bound UI controls ("pods") and flexible layout.

## Key Gaps Filled By This Architecture Pack

- Formal PRD input contract for deterministic generation.
- Governance gates for security/quality/cost before promotion.
- Schema controller pattern replacing risky login-time schema mutation.
- Explicit tenancy isolation model for data, vectors, and blobs.
- Traceability model (`REQ -> artifact -> test -> release`).

