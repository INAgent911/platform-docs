# PRD Catalog

## Scope

This catalog tracks all generated PRDs for the MSP platform and maps them to delivery phases.

## PRD Inventory

| PRD ID | Title | Folder | Target Phase |
|---|---|---|---|
| PRD-ENV-001 | Environment and Platform Foundation | `01-foundation` | phase-0 |
| PRD-DB-001 | Canonical Data Model and Schema Governance | `01-foundation` | phase-1 |
| PRD-SEC-001 | Identity, Access, Security, and Compliance | `01-foundation` | phase-1 |
| PRD-OPS-001 | API, Event, and Integration Standards | `01-foundation` | phase-1 |
| PRD-LC-001 | Discovery and Onboarding | `02-lifecycle/01-discovery-onboarding` | phase-2 |
| PRD-LC-002 | Provisioning | `02-lifecycle/02-provisioning` | phase-2 |
| PRD-LC-003 | Service Delivery, Monitoring, and Alerting | `02-lifecycle/03-service-monitoring` | phase-3 |
| PRD-LC-004 | Ticketing, Incident, and Change Operations | `02-lifecycle/04-operations` | phase-4 |
| PRD-LC-005 | Billing, Quoting, Renewals, and Upsell | `02-lifecycle/05-commercial` | phase-5 |
| PRD-LC-006 | Reporting, Analytics, and Offboarding | `02-lifecycle/06-reporting-offboarding` | phase-5 |
| PRD-UI-001 | UI Customization and Workspaces | `03-experience-ai` | phase-3 |
| PRD-AI-001 | AI Copilot and Automation Orchestration | `03-experience-ai` | phase-4 |
| PRD-BIL-001 | Usage Metering and Cost Transparency | `03-experience-ai` | phase-5 |

## Approval Workflow

1. Resolve open questions in each PRD.
2. Mark front matter `status` to `approved`.
3. Implement PRDs by target phase.
4. Track traceability: `REQ -> Artifact -> Test -> Release`.

