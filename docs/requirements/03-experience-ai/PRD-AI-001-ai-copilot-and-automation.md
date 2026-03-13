---
prd_id: PRD-AI-001
title: AI Copilot and Automation Orchestration
version: 1.0.0
owner: AI Platform Team
status: draft
target_phase: phase-4
date: 2026-03-12
---

## Problem

MSPs need AI assistance and automation for speed, but unsafe retrieval and uncontrolled actions can create security, compliance, and cost risk.

## Goals

- Deliver tenant-safe AI copilots for search, triage, and workflow assistance.
- Enforce policy-bound retrieval and action orchestration.
- Combine AI recommendations with human approval controls.

## Non-Goals

- Fully autonomous ticket closure in phase-4.
- Model training pipelines for all customer data from day one.
- Unconstrained AI tool/plugin execution.

## Personas

- Service Desk Agent
- Automation Engineer
- Tenant Admin

## User Stories

- As an agent, I want AI summaries of incidents and alerts to speed triage.
- As an automation engineer, I want AI-suggested playbooks that can be reviewed before activation.
- As a tenant admin, I want strict controls on what AI can read and execute.

## Functional Requirements

- [REQ-AI-801] AI copilot must support semantic+keyword retrieval for tickets, alerts, CI context, and knowledge articles.
  Rationale: Improve context-rich decision support.
  Priority: must
  Dependencies: REQ-AI-010
- [REQ-AI-802] AI context assembly must enforce tenant and record-level authorization before prompt construction.
  Rationale: Prevent data leakage.
  Priority: must
  Dependencies: REQ-AI-020
- [REQ-AI-803] AI interactions must log prompt metadata, referenced records, model profile, and output trace IDs.
  Rationale: Auditability and incident review.
  Priority: must
  Dependencies: REQ-SEC-031
- [REQ-AUT-801] Trigger gateway must orchestrate event-to-workflow automation with policy checks and approval gates.
  Rationale: Safe automation scaling.
  Priority: must
  Dependencies: REQ-AUT-030
- [REQ-AUT-802] Automation playbooks must support manual, semi-automated, and fully automated modes by policy.
  Rationale: Gradual trust and rollout control.
  Priority: should
  Dependencies: REQ-AUT-801

## Non-Functional Requirements

- [REQ-OPS-801] AI response latency for standard operational queries must meet agreed p95 threshold (threshold currently unspecified).
  Rationale: Keep copilots operationally useful.
  Priority: should
  Dependencies: REQ-OPS-012
- [REQ-OPS-802] AI and workflow services must provide resilient retry and circuit-breaker behavior for downstream dependencies.
  Rationale: Stability under external API failure.
  Priority: must
  Dependencies: REQ-ENV-002

## Data Model Requirements

- [REQ-DB-801] Embedding records must store tenant scope, source reference, embedding version, and policy classification.
  Rationale: Safe retrieval and model lifecycle control.
  Priority: must
  Dependencies: REQ-AI-010
- [REQ-DB-802] Playbook model must store trigger conditions, actions, approval policy, and execution history.
  Rationale: Automation governance.
  Priority: must
  Dependencies: REQ-AUT-801

## Security And Compliance Requirements

- [REQ-SEC-801] Restricted fields must be excluded from embeddings and prompt context by policy.
  Rationale: Data protection and compliance.
  Priority: must
  Dependencies: REQ-SEC-021
- [REQ-SEC-802] AI action execution must require explicit tool scopes and policy checks.
  Rationale: Prevent unsafe external side effects.
  Priority: must
  Dependencies: REQ-SEC-042

## AI/Automation Requirements

- [REQ-AI-804] Persona-aware prompt templates must be supported for dispatcher, technician, account manager, and customer admin roles.
  Rationale: Improve relevance and safety.
  Priority: should
  Dependencies: REQ-AI-802
- [REQ-AUT-803] Playbook simulation mode must support dry-run previews before activation.
  Rationale: Reduce deployment risk.
  Priority: should
  Dependencies: REQ-AUT-802

## UI/UX Requirements

- [REQ-UI-801] Copilot UI must display answer sources, confidence hints, and action options.
  Rationale: Trust and explainability.
  Priority: must
  Dependencies: REQ-AI-801
- [REQ-UI-802] Automation builder UI must expose trigger conditions, approval gates, and test-run output.
  Rationale: Operable low-code automation.
  Priority: should
  Dependencies: REQ-AUT-803

## Integrations

- vector store and retrieval services
- workflow engine and connector registry
- collaboration tools for notifications/actions

## Acceptance Criteria

- Copilot retrieves and cites tenant-authorized context only. (REQ-AI-801, REQ-AI-802, REQ-SEC-801)
- AI interaction audit logs contain required trace metadata. (REQ-AI-803)
- Trigger gateway routes events into policy-checked workflows. (REQ-AUT-801, REQ-SEC-802)
- Playbooks support manual/semi/full modes and dry-run simulation. (REQ-AUT-802, REQ-AUT-803)
- Copilot UI exposes source references and safe action prompts. (REQ-UI-801)
- Restricted fields never appear in embeddings or prompt context. (REQ-SEC-801)

## Telemetry And Billing Signals

- AI request latency, token usage, failure rates
- workflow execution counts, duration, and retry rates
- human-approval vs auto-run ratios
- AI-assisted resolution uplift metrics

## Open Questions

- Approved model provider mix and fallback strategy.
- Default confidence threshold for action suggestions.
- Policy for retaining AI prompts/outputs by tenant tier.

