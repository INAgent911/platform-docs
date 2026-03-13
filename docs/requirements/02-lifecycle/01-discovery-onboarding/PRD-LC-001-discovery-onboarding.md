---
prd_id: PRD-LC-001
title: Discovery and Onboarding
version: 1.0.0
owner: Customer Lifecycle Team
status: approved
target_phase: phase-2
date: 2026-03-12
---

## Problem

MSP onboarding is often inconsistent and manual, causing delayed value realization, poor data quality, and operational rework.

## Goals

- Standardize discovery intake and onboarding execution.
- Reduce time-to-onboard and onboarding failure rate.
- Ensure onboarding data is complete and tenant-safe.

## Non-Goals

- Full sales CRM replacement.
- Industry-specific onboarding variants in first release.
- Automated legal contract authoring.

## Personas

- Sales Engineer
- Onboarding Coordinator
- Customer Admin

## User Stories

- As an onboarding coordinator, I want template-driven onboarding plans so every customer follows a reliable path.
- As a customer admin, I want clear progress visibility and action items in a portal.
- As a sales engineer, I want discovery outputs to flow directly into provisioning and service delivery.

## Functional Requirements

- [REQ-PRV-101] The platform must support structured discovery intake for customer sites, users, assets, service scope, and dependencies.
  Rationale: Ensure operational readiness for provisioning.
  Priority: must
  Dependencies: REQ-DB-010
- [REQ-PRV-102] The platform must provide onboarding project templates with tasks, milestones, dependencies, and ownership.
  Rationale: Standardize execution and reduce misses.
  Priority: must
  Dependencies: REQ-PRV-101
- [REQ-PRV-103] Discovery outputs must create or update customer, site, contact, contract, and SLA records.
  Rationale: Preserve single source of truth.
  Priority: must
  Dependencies: REQ-DB-010
- [REQ-UI-101] The customer portal must expose onboarding status, pending approvals, and key milestone dates.
  Rationale: Improve transparency and collaboration.
  Priority: should
  Dependencies: REQ-PRV-102
- [REQ-PRV-104] Missing prerequisite data must trigger automated reminders and escalation tasks.
  Rationale: Minimize onboarding delays.
  Priority: should
  Dependencies: REQ-AUT-001

## Non-Functional Requirements

- [REQ-OPS-101] Onboarding workflows must support concurrent onboarding projects per tenant (exact concurrency target currently unspecified).
  Rationale: MSPs onboard multiple customers in parallel.
  Priority: should
  Dependencies: REQ-ENV-002
- [REQ-OPS-102] Intake form submissions must be recoverable and auditable.
  Rationale: Prevent data loss and support compliance.
  Priority: must
  Dependencies: REQ-SEC-031

## Data Model Requirements

- [REQ-DB-101] Discovery model must include customer hierarchy, site metadata, contact roles, and onboarding artifact references.
  Rationale: Support downstream automation.
  Priority: must
  Dependencies: REQ-PRV-101
- [REQ-DB-102] Onboarding tasks must capture status, owner, due date, dependency, and escalation state.
  Rationale: Enable reliable project tracking.
  Priority: must
  Dependencies: REQ-PRV-102

## Security And Compliance Requirements

- [REQ-SEC-101] Discovery artifacts containing sensitive information must be access-restricted and encrypted at rest.
  Rationale: Protect customer data.
  Priority: must
  Dependencies: REQ-SEC-020
- [REQ-SEC-102] Customer portal visibility must be tenant-scoped and role-scoped.
  Rationale: Prevent cross-tenant exposure.
  Priority: must
  Dependencies: REQ-SEC-030

## AI/Automation Requirements

- [REQ-AUT-101] Onboarding templates must support automation hooks that create provisioning tasks.
  Rationale: Reduce manual handoff.
  Priority: should
  Dependencies: REQ-PRV-102
- [REQ-AI-101] AI assistant should summarize onboarding risks and missing prerequisites.
  Rationale: Improve coordinator efficiency.
  Priority: could
  Dependencies: REQ-AI-020

## UI/UX Requirements

- [REQ-UI-102] Onboarding UI must provide guided intake with validation and save/resume behavior.
  Rationale: Reduce entry errors and abandonment.
  Priority: must
  Dependencies: REQ-PRV-101
- [REQ-UI-103] Internal and customer views must show progress with role-appropriate detail.
  Rationale: Align expectations and accountability.
  Priority: should
  Dependencies: REQ-UI-101

## Integrations

- CRM/opportunity systems
- e-signature/contract systems
- email and collaboration tools

## Acceptance Criteria

- Discovery intake captures required customer/site/service fields with validation. (REQ-PRV-101, REQ-UI-102)
- Onboarding templates generate executable task plans with dependencies. (REQ-PRV-102, REQ-DB-102)
- Approved onboarding data populates canonical customer records. (REQ-PRV-103, REQ-DB-101)
- Portal shows real-time onboarding progress and approvals. (REQ-UI-101, REQ-UI-103)
- Missing prerequisites trigger reminders/escalations automatically. (REQ-PRV-104, REQ-AUT-101)
- Tenant access boundaries are enforced in portal and API flows. (REQ-SEC-102)

## Telemetry And Billing Signals

- time-to-onboard
- task completion SLA and overdue counts
- onboarding rework rate
- portal engagement during onboarding

## Open Questions

- None. Resolved decisions:
- Decision: Onboarding SLA targets are SMB (<=100 endpoints)=10 business days, Mid-market (101-1000)=20 business days, Enterprise (>1000)=45 business days.
- Decision: Required onboarding template variants are Core, Regulated (healthcare/finance), Public Sector, and Co-managed IT.
- Decision: Customer-facing artifacts include milestone status/approvals/timelines; internal-only artifacts include credential details, security findings, and escalation notes.
