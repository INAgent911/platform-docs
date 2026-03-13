---
prd_id: PRD-BIL-001
title: Usage Metering and Cost Transparency
version: 1.0.0
owner: Finance Platform Team
status: approved
target_phase: phase-5
date: 2026-03-12
---

## Problem

MSPs adopting AI and automation need transparent usage economics; without explainable metering, trust and adoption drop.

## Goals

- Meter compute/storage/workflow/token usage accurately.
- Expose real-time and historical cost transparency to tenants.
- Link usage signals to billing and optimization recommendations.

## Non-Goals

- Full enterprise cost accounting replacement.
- Real-time invoicing for every event in phase-5.
- Automatic price adjustments without governance.

## Personas

- Tenant Owner
- Billing Administrator
- Platform Finance Analyst

## User Stories

- As a tenant owner, I want to understand what drove this month’s charges.
- As a billing admin, I want usage lines to reconcile with invoices.
- As a finance analyst, I want cost anomaly alerts before overrun.

## Functional Requirements

- [REQ-BIL-801] The platform must meter token usage, workflow executions, API compute units, and storage consumption per tenant.
  Rationale: Accurate usage-based charging.
  Priority: must
  Dependencies: REQ-BIL-101
- [REQ-BIL-802] Usage events must map to billable dimensions and pricing catalog versions.
  Rationale: Reproducible billing calculations.
  Priority: must
  Dependencies: REQ-DB-502
- [REQ-BIL-803] Tenant-facing usage dashboard must show near-real-time usage and projected monthly cost.
  Rationale: Reduce bill shock and support planning.
  Priority: must
  Dependencies: REQ-UI-501
- [REQ-BIL-804] Cost anomaly rules must generate alerts and recommended mitigation actions.
  Rationale: Prevent runaway spend.
  Priority: should
  Dependencies: REQ-AI-601
- [REQ-BIL-805] Usage exports must support finance reconciliation workflows.
  Rationale: Audit and reporting compatibility.
  Priority: should
  Dependencies: REQ-OPS-602

## Non-Functional Requirements

- [REQ-OPS-901] Metering ingestion pipeline must be loss-resistant and idempotent.
  Rationale: Prevent billing inaccuracies.
  Priority: must
  Dependencies: REQ-OPS-032
- [REQ-OPS-902] Usage dashboard freshness SLO must be defined and monitored (SLO currently unspecified).
  Rationale: Trust in visibility.
  Priority: should
  Dependencies: REQ-BIL-803

## Data Model Requirements

- [REQ-DB-901] Usage ledger must store tenant_id, meter_type, quantity, unit_cost_basis, time window, and trace_id.
  Rationale: Reconciliation and explainability.
  Priority: must
  Dependencies: REQ-BIL-801
- [REQ-DB-902] Cost summary model must support aggregation by customer, service, workflow, and AI feature.
  Rationale: Operational and financial insight.
  Priority: must
  Dependencies: REQ-BIL-803

## Security And Compliance Requirements

- [REQ-SEC-901] Usage and billing data access must be role-scoped and tenant-scoped.
  Rationale: Protect financial data.
  Priority: must
  Dependencies: REQ-SEC-030
- [REQ-SEC-902] Metering event integrity must be verifiable and tamper-evident.
  Rationale: Billing trust and audit readiness.
  Priority: must
  Dependencies: REQ-SEC-031

## AI/Automation Requirements

- [REQ-AI-901] AI assistant should provide natural-language billing summaries referencing usage drivers.
  Rationale: Improve comprehension for non-technical stakeholders.
  Priority: should
  Dependencies: REQ-BIL-803
- [REQ-AUT-901] Automation should recommend cost optimizations such as threshold tuning, schedule changes, and model profile changes.
  Rationale: Ongoing efficiency.
  Priority: could
  Dependencies: REQ-BIL-804

## UI/UX Requirements

- [REQ-UI-901] Cost dashboard must provide drill-down from invoice lines to usage events.
  Rationale: Explainability and dispute resolution.
  Priority: must
  Dependencies: REQ-BIL-802
- [REQ-UI-902] Budget controls UI must allow tenant admins to define alerts and hard/soft spending thresholds.
  Rationale: Spend governance.
  Priority: should
  Dependencies: REQ-BIL-804

## Integrations

- billing/invoicing services
- data warehouse/reporting systems
- notification channels for anomaly alerts

## Acceptance Criteria

- Metering captures required usage classes per tenant with traceability. (REQ-BIL-801, REQ-DB-901)
- Usage-to-price mapping is reproducible against catalog versions. (REQ-BIL-802)
- Dashboard shows current period usage, projected cost, and drill-down detail. (REQ-BIL-803, REQ-UI-901)
- Cost anomalies generate alerts and recommendations. (REQ-BIL-804, REQ-AUT-901)
- Exported usage reconciles with invoice lines in audit sample tests. (REQ-BIL-805)
- Meter events are tamper-evident and access-controlled. (REQ-SEC-901, REQ-SEC-902)

## Telemetry And Billing Signals

- metering ingestion lag and drop rate
- usage-to-invoice reconciliation variance
- anomaly alert volume and resolution
- budget-threshold breach frequency

## Open Questions

- None. Resolved decisions:
- Decision: Usage dashboard freshness target is p95 <=5 minutes with hard maximum lag of 15 minutes.
- Decision: Default anomaly sensitivity is standard tier +30% over 7-day baseline, growth tier +20%, enterprise tier +10% with hourly evaluation.
- Decision: Detailed usage events are retained 25 months; monthly rollups are retained 7 years.
