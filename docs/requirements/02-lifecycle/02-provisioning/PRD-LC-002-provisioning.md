---
prd_id: PRD-LC-002
title: Provisioning
version: 1.0.0
owner: Customer Lifecycle Team
status: approved
target_phase: phase-2
date: 2026-03-12
---

## Problem

Provisioning failures create service delays, misconfiguration risk, and repeated manual corrections across tenant environments.

## Goals

- Automate provisioning runbooks and approvals.
- Ensure tenant-safe, idempotent provisioning execution.
- Link provisioning outcomes to CMDB and monitoring enrollment.

## Non-Goals

- Full zero-touch provisioning for every integration in phase-2.
- Custom scripting engines per tenant.
- Autonomous privileged action without approval controls.

## Personas

- Provisioning Technician
- Security Approver
- Customer Admin

## User Stories

- As a technician, I need runbooks so account/service setup is repeatable.
- As a security approver, I need approval gates for privileged provisioning.
- As a customer admin, I need status and confirmations of completed setup.

## Functional Requirements

- [REQ-PRV-201] Provisioning service must accept tenant bootstrap requests with authorized first-user email restrictions.
  Rationale: Enforce initial ownership control.
  Priority: must
  Dependencies: REQ-USR-001
- [REQ-PRV-202] Provisioning workflows must include account creation, policy baseline application, monitoring enrollment, and CMDB registration.
  Rationale: Establish operational baseline at activation.
  Priority: must
  Dependencies: REQ-DB-017
- [REQ-PRV-203] Provisioning tasks must be idempotent and retryable.
  Rationale: Support resilience under transient failures.
  Priority: must
  Dependencies: REQ-OPS-032
- [REQ-PRV-204] Provisioning must consume content/base packages for standard tenant capabilities.
  Rationale: Accelerate onboarding and consistency.
  Priority: should
  Dependencies: REQ-AUT-101
- [REQ-PRV-205] Privileged provisioning actions must enforce approval policies before execution.
  Rationale: Reduce security risk.
  Priority: must
  Dependencies: REQ-SEC-030

## Non-Functional Requirements

- [REQ-OPS-201] Provisioning pipeline must expose step-level status, retries, and failure diagnostics.
  Rationale: Improve supportability.
  Priority: must
  Dependencies: REQ-PRV-202
- [REQ-OPS-202] Provisioning workflows must support burst execution per tenant without cross-tenant interference (burst target currently unspecified).
  Rationale: MSPs often onboard batches.
  Priority: should
  Dependencies: REQ-ENV-002

## Data Model Requirements

- [REQ-DB-201] Provisioning model must track request, step, actor, approval state, and final outcome.
  Rationale: Traceability and audit.
  Priority: must
  Dependencies: REQ-PRV-202
- [REQ-DB-202] Provisioned assets and service bindings must be linked to customer site and CI records.
  Rationale: Impact analysis and support continuity.
  Priority: must
  Dependencies: REQ-DB-017

## Security And Compliance Requirements

- [REQ-SEC-201] Provisioning credentials and tokens must be ephemeral and never exposed in logs.
  Rationale: Prevent credential leakage.
  Priority: must
  Dependencies: REQ-SEC-002
- [REQ-SEC-202] Provisioning executions must be tenant-bound by policy and identifier checks.
  Rationale: Avoid wrong-tenant actions.
  Priority: must
  Dependencies: REQ-SEC-020

## AI/Automation Requirements

- [REQ-AUT-201] Trigger gateway must convert onboarding completion events into provisioning actions.
  Rationale: Eliminate manual handoffs.
  Priority: should
  Dependencies: REQ-PRV-102
- [REQ-AI-201] AI assistant should propose remediation steps for failed provisioning runs using runbook history.
  Rationale: Speed up recovery.
  Priority: could
  Dependencies: REQ-AI-101

## UI/UX Requirements

- [REQ-UI-201] Provisioning console must show runbook steps, approvals, and rollback options.
  Rationale: Safe operations.
  Priority: must
  Dependencies: REQ-OPS-201
- [REQ-UI-202] Customer-facing status must show milestone completion and expected next actions.
  Rationale: Improve trust and readiness.
  Priority: should
  Dependencies: REQ-PRV-202

## Integrations

- identity/directory systems
- CMDB and monitoring services
- notification channels (email/chat)

## Acceptance Criteria

- First-user email restriction is enforced during tenant bootstrap. (REQ-PRV-201)
- Standard provisioning workflow completes with account, monitoring, and CMDB updates. (REQ-PRV-202, REQ-DB-202)
- Duplicate provisioning requests with same idempotency key do not duplicate side effects. (REQ-PRV-203)
- Privileged actions are blocked without required approvals. (REQ-PRV-205, REQ-SEC-202)
- Step-level diagnostics are available for failures and retries. (REQ-OPS-201)
- Credentials are masked and not persisted in logs. (REQ-SEC-201)

## Telemetry And Billing Signals

- provisioning lead time and success rate
- retry rate and failure reason distribution
- automation ratio (auto vs manual steps)
- per-tenant provisioning compute costs

## Open Questions

- None. Resolved decisions:
- Decision: Standard catalog provisioning is auto-approved; privileged provisioning requires dual approval (security approver plus tenant owner/admin).
- Decision: Provisioning SLA targets are standard activation <=4 business hours, complex bundle <=1 business day, endpoint rollout 95% complete <=24 hours.
- Decision: Rollback depth must support per-step compensation plus full workflow rollback to last known good state when feasible.
