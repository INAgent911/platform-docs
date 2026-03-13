# PRD Input Contract (For Deterministic Generation)

Use this structure for each PRD that should drive generated platform changes.

## Required Front Matter

```yaml
prd_id: PRD-XXXX
title: <short title>
version: 1.0.0
owner: <team or person>
status: draft|approved
target_phase: phase-0|phase-1|phase-2|phase-3|phase-4|phase-5
date: YYYY-MM-DD
```

## Required Sections

1. `Problem`
2. `Goals`
3. `Non-Goals`
4. `Personas`
5. `User Stories`
6. `Functional Requirements`
7. `Non-Functional Requirements`
8. `Data Model Requirements`
9. `Security And Compliance Requirements`
10. `AI/Automation Requirements`
11. `UI/UX Requirements`
12. `Integrations`
13. `Acceptance Criteria`
14. `Telemetry And Billing Signals`
15. `Open Questions`

## Requirement ID Rules

- Every requirement must have a unique ID.
- ID format: `REQ-<DOMAIN>-<NUMBER>` (example: `REQ-UI-014`).
- Every acceptance criterion references one or more requirement IDs.

## Requirement Statement Format

```text
[REQ-<DOMAIN>-<N>] <clear requirement statement>
Rationale:
Priority: must|should|could
Dependencies:
```

## Domain Tags

- `ENV` environment/deployment
- `DB` data/schema/storage
- `USR` users/identity
- `PRV` provisioning
- `UI` customization/experience
- `AI` search/copilot/vectorization
- `AUT` automation/workflow
- `SEC` security/compliance
- `OPS` observability/reliability
- `BIL` billing/usage

## Example Minimal PRD Snippet

```markdown
[REQ-DB-001] The platform must support YAML-defined entity schemas with controlled migrations.
Rationale: Enable no-code extensibility while preserving stability.
Priority: must
Dependencies: REQ-SEC-003, REQ-OPS-002

[REQ-USR-004] The first tenant user created during provisioning must become owner.
Rationale: Enforce explicit tenant accountability.
Priority: must
Dependencies: REQ-PRV-002
```

## Generator Output Expectations

For each approved PRD, the generator should produce:
- architecture delta summary
- schema/API/UI/workflow contract updates
- migration scripts
- tests
- release notes
- traceability map: `REQ -> artifacts -> tests`

## Rejection Conditions

A PRD should be rejected or sent back for revision if:
- required sections are missing
- requirements are unnumbered or ambiguous
- acceptance criteria do not map to requirements
- required security or tenancy constraints are absent

