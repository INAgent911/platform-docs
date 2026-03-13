---
prd_id: PRD-DB-001
title: Canonical Data Model and Schema Governance
version: 1.0.0
owner: Data Platform Team
status: draft
target_phase: phase-1
date: 2026-03-12
---

## Problem

The platform requires a canonical customer-centered data model and controlled schema evolution so tenant customization does not break reporting, integrations, or AI workflows.

## Goals

- Implement a canonical entity model centered on customer lifecycle.
- Enforce schema governance through YAML contracts and controlled migrations.
- Support multi-tenant isolation with benchmark-safe standardization.

## Non-Goals

- Real-time global cross-tenant joins in phase-1.
- Full ontology automation for every vertical on day one.
- Unrestricted free-form schema mutation at runtime.

## Personas

- Data Architect
- Platform Engineer
- Reporting Analyst

## User Stories

- As a data architect, I want canonical entities so integrations are stable.
- As an engineer, I want schema migrations generated from manifests so changes are predictable.
- As an analyst, I want standardized dimensions so benchmarking is meaningful.

## Functional Requirements

- [REQ-DB-010] The platform must implement canonical entities including CustomerAccount, Site, Contact, Contract, SLA, CI, Event, Alert, Ticket, ChangeRequest, Invoice, Renewal, and AuditEvent.
  Rationale: Align platform data to lifecycle operations and reporting.
  Priority: must
  Dependencies: none
- [REQ-DB-011] Schema definitions must be authored in YAML and validated before migration generation.
  Rationale: Support deterministic PRD-driven schema change.
  Priority: must
  Dependencies: REQ-OPS-011
- [REQ-DB-012] Schema changes must execute through a Schema Controller service, not at login time.
  Rationale: Prevent uncontrolled production mutations.
  Priority: must
  Dependencies: REQ-DB-011
- [REQ-DB-013] The platform must support extension patterns for tenant custom fields while preserving core canonical entities.
  Rationale: Balance customization with data quality.
  Priority: must
  Dependencies: REQ-DB-010
- [REQ-DB-014] Deprecation windows for removed fields must be at least 365 days unless explicitly waived.
  Rationale: Protect downstream integrations and historical analytics.
  Priority: must
  Dependencies: REQ-DB-012
- [REQ-DB-015] Blob/file payloads must be stored in object storage with hash-based de-duplication and metadata references in database.
  Rationale: Improve performance and storage efficiency.
  Priority: should
  Dependencies: REQ-ENV-002

## Non-Functional Requirements

- [REQ-OPS-010] Schema migration preflight tests must run before every apply operation.
  Rationale: Catch breaking changes early.
  Priority: must
  Dependencies: REQ-DB-012
- [REQ-OPS-011] YAML validation and migration generation must be deterministic for identical inputs.
  Rationale: Required for reproducible builds.
  Priority: must
  Dependencies: none
- [REQ-OPS-012] Core read queries for customer/ticket/alert flows must meet p95 under 300 ms at target load (load targets currently unspecified).
  Rationale: Support responsive operations.
  Priority: should
  Dependencies: REQ-DB-010

## Data Model Requirements

- [REQ-DB-016] Every tenant-scoped operational record must include `tenant_id` and immutable creation metadata.
  Rationale: Enforce isolation and traceability.
  Priority: must
  Dependencies: REQ-SEC-020
- [REQ-DB-017] CI relationship graph must support impact analysis for incidents and changes.
  Rationale: Required for ITIL-aligned operations.
  Priority: must
  Dependencies: REQ-DB-010
- [REQ-DB-018] Event and alert records must support normalization to a standard event envelope.
  Rationale: Simplify vendor heterogeneity.
  Priority: must
  Dependencies: REQ-OPS-020

## Security And Compliance Requirements

- [REQ-SEC-020] Database access must enforce tenant boundary policies and least-privilege service accounts.
  Rationale: Prevent cross-tenant leakage.
  Priority: must
  Dependencies: none
- [REQ-SEC-021] Sensitive fields must support classification tags and policy-based handling (masking, encryption, exclusion from vectorization).
  Rationale: GDPR/SOC2 aligned controls.
  Priority: must
  Dependencies: REQ-AI-010
- [REQ-SEC-022] Data retention and deletion rules must be policy-driven per entity class.
  Rationale: Compliance and offboarding obligations.
  Priority: should
  Dependencies: REQ-PRV-602

## AI/Automation Requirements

- [REQ-AI-010] Vectorization eligibility must be field-level and allow/deny policy driven from schema manifest.
  Rationale: Control cost and privacy risk.
  Priority: must
  Dependencies: REQ-DB-011
- [REQ-AUT-010] Schema change events must be emitted for downstream automation (indexing, cache invalidation, reporting refresh).
  Rationale: Keep derived systems synchronized.
  Priority: should
  Dependencies: REQ-DB-012

## UI/UX Requirements

- [REQ-UI-010] Schema administration UI must show diff, risk flags, migration plan, and rollback plan before apply.
  Rationale: Improve operator confidence and safety.
  Priority: should
  Dependencies: REQ-DB-012
- [REQ-UI-011] Data model explorer must visualize canonical entities and relationships.
  Rationale: Support onboarding and troubleshooting.
  Priority: should
  Dependencies: REQ-DB-017

## Integrations

- Postgres and object storage
- Schema registry and migration toolchain
- Event bus for schema lifecycle events

## Acceptance Criteria

- Canonical entity set is represented in schema manifests and database tables. (REQ-DB-010)
- Schema changes are rejected if they bypass controller validation. (REQ-DB-012, REQ-OPS-010)
- Tenant custom fields work without modifying core canonical tables. (REQ-DB-013)
- Field deprecations enforce minimum retention window. (REQ-DB-014)
- Blob objects are reference-linked and deduplicated by hash. (REQ-DB-015)
- Vectorization policy blocks restricted fields from embedding pipelines. (REQ-AI-010, REQ-SEC-021)

## Telemetry And Billing Signals

- migration success/failure counts
- schema validation error rates by rule
- query latency by entity family
- blob deduplication ratio and storage growth

## Open Questions

- Preferred representation for tenant extensions: JSONB-first vs generated typed columns.
- Final canonical ontology for benchmarking dimensions.
- Data residency partitioning model by region.
