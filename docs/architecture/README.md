# PRD-Driven Platform Architecture

This folder defines the architecture for an MSP-oriented SaaS platform that is generated from Product Requirements Documents (PRDs), then implemented in iterative Codex sessions.

Source baseline used to shape this pack:
- Confluence export pages: `MSP Platform Vision`, `Environment`, `Database`, `Users`, `Provisioning`, `Views Customization`, `Design Methodology`, `Initial Critique from partial ideas`.
- Key intent: AI-native, highly customizable, multi-tenant, secure, workflow-enabled, and ready for repeatable code generation.

## How To Use This Pack

1. Review all files in this folder and adjust assumptions.
2. Freeze or version this folder snapshot as the target architecture for a build phase.
3. Feed these markdown files back into Codex with a scoped implementation request (for example: "build Phase 1, Environment + Users").
4. Keep implementation output traceable to these docs by requirement ID and decision ID.

## Document Map

- [00-requirements-baseline.md](/C:/source/platform-docs/docs/architecture/00-requirements-baseline.md)
- [01-prd-driven-platform-architecture.md](/C:/source/platform-docs/docs/architecture/01-prd-driven-platform-architecture.md)
- [02-generation-pipeline-and-governance.md](/C:/source/platform-docs/docs/architecture/02-generation-pipeline-and-governance.md)
- [03-data-schema-and-ai-architecture.md](/C:/source/platform-docs/docs/architecture/03-data-schema-and-ai-architecture.md)
- [04-application-security-ui-automation-ops.md](/C:/source/platform-docs/docs/architecture/04-application-security-ui-automation-ops.md)
- [05-roadmap-and-execution.md](/C:/source/platform-docs/docs/architecture/05-roadmap-and-execution.md)
- [contracts/prd-input-contract.md](/C:/source/platform-docs/docs/architecture/contracts/prd-input-contract.md)

## Architecture Goals

- Generate platform behavior from PRDs and controlled YAML/JSON manifests.
- Support secure multi-tenant MSP operations with record-level authorization.
- Deliver AI + vector search + workflow automation as first-class platform capabilities.
- Keep customization powerful while preserving standards for benchmarking/reporting.
- Make implementation reproducible, testable, and auditable.

## Out Of Scope (For Initial Build)

- Full marketplace monetization.
- Advanced remote agent management suite.
- Complex cross-cloud deployment.
- Fully autonomous AI code merge without human approval.
