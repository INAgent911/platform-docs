# 05. Roadmap And Execution Plan

## 1) Delivery Strategy

Use a phased approach that aligns with your stated design order while keeping scope controlled.

## 2) Phase Plan

### Phase 0: Foundation (Environment)

Outcomes:
- Local Docker runtime and Azure deployment baseline.
- CI/CD skeleton and policy/test gates.
- Core service templates (API gateway, identity service, schema controller shell).

Exit criteria:
- one-click local startup
- non-prod deployment pipeline running
- baseline observability online

### Phase 1: Data And Identity (Database + Users)

Outcomes:
- YAML schema contract and Schema Controller MVP.
- Postgres tenant model with RLS.
- User auth, MFA hooks, owner bootstrap flow.

Exit criteria:
- schema manifest applies safely through pipeline
- user login and role enforcement working
- audit trail for user and schema changes

### Phase 2: Tenant Bootstrap (Provisioning)

Outcomes:
- provisioning service accepts allowed first-user email
- base package installation flow
- tenant initialization jobs + status tracking

Exit criteria:
- tenant can be provisioned end-to-end by API/UI flow
- provisioning failures are recoverable and observable

### Phase 3: UI Customization (Views/Pods/Shell)

Outcomes:
- 3-level nav shell, top bar, breadcrumbs
- theme branding controls (light/dark, logo, color tokens)
- view manifest support for layouts and shared/personal views

Exit criteria:
- at least 2 role-specific workspace views
- UI changes versioned and rollback-capable

### Phase 4: AI + Workflow Core

Outcomes:
- vectorization policy enforcement
- semantic + keyword search
- trigger gateway and workflow engine integration
- first AI playbook scenarios

Exit criteria:
- AI retrieval honors record-level permissions
- 3 production-grade workflow templates available

### Phase 5: Reporting, Benchmarking, Billing

Outcomes:
- reporting dashboards and benchmark taxonomy scaffolding
- usage metering + cost transparency
- tenant-level billing event exports

Exit criteria:
- usage dashboard and cost attribution functional
- benchmark data pipelines validated

## 3) MVP Recommendation

Start with an `AI-Native Ticketing + Workflow` slice:
- ticket schema from YAML
- user/role access
- customizable ticket board view
- stale-ticket escalation workflow
- AI-assisted ticket search/summarization

This exercises the highest-risk architecture seams early: schema, tenancy, AI, workflow, security, and UI customization.

## 4) Risk Register

- Scope creep from broad vision.
  - Mitigation: phase gates, strict MVP slice, requirement freeze per sprint.
- Dynamic schema instability.
  - Mitigation: schema controller, compatibility checks, staged rollouts.
- AI safety and leakage.
  - Mitigation: policy-bound retrieval, audit logs, red-team tests.
- Cost unpredictability.
  - Mitigation: usage budgets, semantic caching, metering-first design.

## 5) Execution Workflow (Codex + Jira + Confluence)

Per feature cycle:
1. select scoped requirements from this architecture pack
2. generate implementation branch plan
3. create Jira epic/tasks from requirement IDs
4. implement with tests and policy checks
5. publish docs/change summary for human approval
6. merge and promote

## 6) How To Feed This Back To Codex Later

When you are ready to implement, pass:
- this full folder (`docs/architecture`)
- target phase (for example: `Phase 1`)
- stack preference confirmation (Python/React/Postgres/Azure)
- repo constraints (monorepo vs polyrepo)

Recommended request template:

```text
Using /docs/architecture as the source of truth, implement Phase <N>.
Requirements:
- map every change to REQ/ADR IDs from architecture docs
- generate migrations/contracts/tests/docs
- keep changes deployable in Docker and Azure
- stop if a decision is ambiguous and propose ADR options
```

## 7) Immediate Next Step

Finalize any architecture decisions you want fixed before implementation:
- workflow engine choice (Camunda vs n8n)
- vector store initial choice (pgvector-only vs pgvector+Qdrant)
- identity provider approach (built-in first vs external IdP-first)

