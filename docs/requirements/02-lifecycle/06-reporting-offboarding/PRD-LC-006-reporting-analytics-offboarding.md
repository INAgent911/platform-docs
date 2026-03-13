---
prd_id: PRD-LC-006
title: Reporting, Analytics, and Offboarding
version: 1.0.0
owner: Insights and Governance Team
status: approved
target_phase: phase-5
date: 2026-03-12
---

## Problem

MSPs need trustworthy reporting for SLA and business performance, plus controlled offboarding for data export/deletion obligations; both are often fragmented and risky.

## Goals

- Deliver unified operational and commercial analytics.
- Provide audit-ready exports and tenant-safe reporting.
- Execute controlled offboarding with verifiable access removal and data handling.

## Non-Goals

- Full enterprise BI replacement.
- Cross-tenant benchmarking without governance controls.
- Fully automated legal/compliance interpretation.

## Personas

- Operations Manager
- Executive Sponsor
- Offboarding Coordinator

## User Stories

- As an operations manager, I need SLA and trend reporting with drill-down context.
- As an executive, I need profitability and service quality visibility by customer.
- As an offboarding coordinator, I need a verifiable deprovision/export checklist.

## Functional Requirements

- [REQ-OPS-601] The platform must provide unified KPI dashboards for SLA attainment, MTTR, MTTD, ticket trends, and service performance.
  Rationale: Continuous service improvement.
  Priority: must
  Dependencies: REQ-OPS-301, REQ-OPS-401
- [REQ-OPS-602] Reporting must support customer-, site-, and service-level drill-down with export capability.
  Rationale: Actionable accountability.
  Priority: must
  Dependencies: REQ-DB-010
- [REQ-PRV-601] Offboarding workflows must support deprovisioning, credential rotation, monitoring removal, and closure confirmation.
  Rationale: Safe customer separation.
  Priority: must
  Dependencies: REQ-PRV-202
- [REQ-PRV-602] Offboarding must support machine-readable data export packages for customer records.
  Rationale: Contract and portability obligations.
  Priority: must
  Dependencies: REQ-SEC-034
- [REQ-PRV-603] Offboarding completion must require checklist validation and sign-off evidence.
  Rationale: Avoid residual access risk.
  Priority: must
  Dependencies: REQ-PRV-601

## Non-Functional Requirements

- [REQ-OPS-603] Report generation and dashboard queries must meet agreed freshness/latency targets (targets currently unspecified).
  Rationale: Decision quality depends on timely data.
  Priority: should
  Dependencies: REQ-OPS-601
- [REQ-OPS-604] Offboarding operations must be recoverable and restart-safe.
  Rationale: Prevent partial decommission failures.
  Priority: must
  Dependencies: REQ-PRV-603

## Data Model Requirements

- [REQ-DB-601] Analytics model must include curated metric definitions with lineage back to operational/commercial source entities.
  Rationale: Metric trust and auditability.
  Priority: must
  Dependencies: REQ-OPS-601
- [REQ-DB-602] Offboarding model must track export requests, dataset manifests, deletion actions, and approval artifacts.
  Rationale: Compliance evidence.
  Priority: must
  Dependencies: REQ-PRV-602

## Security And Compliance Requirements

- [REQ-SEC-601] Reporting access must enforce tenant-scoped row filtering and role-based visibility.
  Rationale: Prevent leakage and inference.
  Priority: must
  Dependencies: REQ-SEC-030
- [REQ-SEC-602] Offboarding must support policy-based data retention, deletion, and legal-hold exceptions.
  Rationale: Regulatory and contractual alignment.
  Priority: must
  Dependencies: REQ-SEC-034

## AI/Automation Requirements

- [REQ-AI-601] AI assistant should generate narrative summaries for KPI trends and service review prep.
  Rationale: Reduce reporting overhead.
  Priority: should
  Dependencies: REQ-AI-301
- [REQ-AUT-601] Offboarding workflow must automate checklist sequencing and dependency validation.
  Rationale: Reduce manual process errors.
  Priority: should
  Dependencies: REQ-PRV-603

## UI/UX Requirements

- [REQ-UI-601] Reporting UI must provide executive and operational presets with drill-through links.
  Rationale: Match different decision workflows.
  Priority: should
  Dependencies: REQ-OPS-601
- [REQ-UI-602] Offboarding UI must provide clear progress, pending items, and verification status.
  Rationale: Confidence and operational control.
  Priority: should
  Dependencies: REQ-PRV-603

## Integrations

- BI/export tools
- identity/deprovisioning systems
- storage and archival services

## Acceptance Criteria

- KPI dashboards and exports are available for customer/site/service scopes. (REQ-OPS-601, REQ-OPS-602)
- Metric lineage can be traced from dashboard values to source records. (REQ-DB-601)
- Offboarding workflow executes deprovisioning and verification checklist fully. (REQ-PRV-601, REQ-PRV-603)
- Data export package is generated with manifest and integrity checks. (REQ-PRV-602, REQ-DB-602)
- Retention/deletion policies and legal-hold behavior are enforced. (REQ-SEC-602)
- Tenant scope controls prevent cross-tenant reporting access. (REQ-SEC-601)

## Telemetry And Billing Signals

- dashboard freshness lag
- report generation success/failure
- offboarding cycle time and exception rate
- export volume and completion integrity

## Open Questions

- None. Resolved decisions:
- Decision: Default KPI catalog includes executive KPIs (ARR, margin, churn, NRR), operations KPIs (SLA attainment, MTTR/MTTD, backlog), and finance KPIs (DSO, invoice accuracy, leakage) with tier-based depth.
- Decision: Required offboarding evidence package includes deprovision checklist, access revocation logs, export manifest with hashes, deletion/retention certificate, final billing reconciliation, and signed approvals.
- Decision: Former-tenant archival policy is operational data cold-archived for 13 months, financial/audit records retained 7 years, with GDPR erasure workflow and legal-hold override support.
