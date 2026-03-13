---
prd_id: PRD-LC-004
title: Ticketing, Incident, and Change Operations
version: 1.0.0
owner: Service Operations Team
status: approved
target_phase: phase-4
date: 2026-03-12
---

## Problem

Without disciplined incident and change workflows, MSP operations suffer higher downtime, poor escalation quality, and recurring preventable failures.

## Goals

- Implement ITIL-aligned incident and change lifecycle controls.
- Improve MTTR and change success rate.
- Strengthen governance, approvals, and post-incident learning.

## Non-Goals

- Full ITSM suite parity in first release.
- Fully autonomous major-incident management.
- Industry-specific regulatory reporting in phase-4.

## Personas

- Incident Manager
- Change Manager
- Service Desk Agent

## User Stories

- As an incident manager, I need clear escalation and communication workflows for major incidents.
- As a change manager, I need risk scoring and approvals before production changes.
- As an agent, I need ticket templates and knowledge suggestions to resolve faster.

## Functional Requirements

- [REQ-OPS-401] Ticketing must support intake, categorization, prioritization, assignment, escalation, resolution, and closure workflows.
  Rationale: Core service desk capability.
  Priority: must
  Dependencies: REQ-OPS-301
- [REQ-OPS-402] Incident workflows must support major incident mode, stakeholder updates, and post-incident review artifacts.
  Rationale: Minimize service impact and improve learning.
  Priority: must
  Dependencies: REQ-OPS-401
- [REQ-OPS-403] Change management must support standard/normal/emergency types with risk assessment, approval, scheduling, and rollback planning.
  Rationale: Reduce change-related incidents.
  Priority: must
  Dependencies: REQ-DB-017
- [REQ-OPS-404] Ticket, incident, and change records must link to affected CIs and contracts.
  Rationale: Impact awareness and entitlement clarity.
  Priority: should
  Dependencies: REQ-DB-010
- [REQ-AUT-401] Standard low-risk changes must be automatable through approved runbooks.
  Rationale: Improve speed and consistency.
  Priority: should
  Dependencies: REQ-OPS-403

## Non-Functional Requirements

- [REQ-OPS-405] The platform must sustain incident spike handling with stable queue and search performance.
  Rationale: Major incidents create sudden load.
  Priority: must
  Dependencies: REQ-OPS-306
- [REQ-OPS-406] SLA clocks and escalation timers must be deterministic and auditable.
  Rationale: Contract accountability.
  Priority: must
  Dependencies: REQ-DB-302

## Data Model Requirements

- [REQ-DB-401] Incident and change records must include timeline events, approvals, communications, and linked evidence.
  Rationale: Auditability and retrospective analysis.
  Priority: must
  Dependencies: REQ-OPS-402
- [REQ-DB-402] Knowledge references and known-error links must be attachable to tickets/incidents.
  Rationale: Accelerate repeat issue resolution.
  Priority: should
  Dependencies: REQ-OPS-401

## Security And Compliance Requirements

- [REQ-SEC-401] Change approvals must enforce segregation of duties for privileged production actions.
  Rationale: Governance and risk reduction.
  Priority: must
  Dependencies: REQ-SEC-030
- [REQ-SEC-402] Incident and change records must maintain immutable action history.
  Rationale: Compliance and forensics.
  Priority: must
  Dependencies: REQ-SEC-031

## AI/Automation Requirements

- [REQ-AI-401] AI assistant should suggest likely root cause categories and relevant runbooks/knowledge for incidents.
  Rationale: Improve triage speed.
  Priority: should
  Dependencies: REQ-AI-301
- [REQ-AUT-402] Change risk scoring should support rules-based and AI-assisted recommendations with human approval.
  Rationale: Improve decision quality while preserving control.
  Priority: should
  Dependencies: REQ-OPS-403

## UI/UX Requirements

- [REQ-UI-401] Operations workspace must provide war-room and change-calendar views with dependency context.
  Rationale: Faster coordination and safer scheduling.
  Priority: should
  Dependencies: REQ-OPS-402
- [REQ-UI-402] Customer status updates must be generated from incident timelines with role-safe messaging.
  Rationale: Improve communication quality.
  Priority: should
  Dependencies: REQ-OPS-402

## Integrations

- monitoring/alert platforms
- collaboration and status communication tools
- CI/CD or deployment systems for change execution

## Acceptance Criteria

- Ticket lifecycle works end-to-end with SLA clocks and escalation routing. (REQ-OPS-401, REQ-OPS-406)
- Major incident mode supports communication cadence and PIR artifact generation. (REQ-OPS-402, REQ-DB-401)
- Change workflow enforces risk scoring, approvals, and rollback plan requirement. (REQ-OPS-403, REQ-SEC-401)
- Ticket/incident/change entities link to CIs and contracts. (REQ-OPS-404)
- Standard approved changes can execute via runbooks with full audit trail. (REQ-AUT-401, REQ-SEC-402)
- Incident spike load test validates queue/search stability. (REQ-OPS-405)

## Telemetry And Billing Signals

- MTTR by priority/severity
- change success/failure/rollback rates
- major incident frequency and duration
- communication timeliness SLA

## Open Questions

- None. Resolved decisions:
- Decision: Default SLA matrix is P1 response=15m resolve=4h, P2 response=30m resolve=8h, P3 response=4h resolve=2 business days, P4 response=1 business day resolve=5 business days.
- Decision: CAB depth is standard tier single approver for low-risk changes, regulated/enterprise tier quorum of 3 approvers (change, security, customer rep) for high-risk changes, emergency changes require post-implementation review within 24h.
- Decision: Incident customer communications follow P1 every 30m, P2 hourly, P3 every 4h, P4 daily or on major status change.
