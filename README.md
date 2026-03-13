# MSP Platform

This repository now contains:
- approved architecture and PRD documentation
- a no-cost local-first implementation baseline (API + web + Postgres)

## Docs

- [Architecture](/C:/source/platform-docs/docs/architecture/README.md)
- [Requirements and PRDs](/C:/source/platform-docs/docs/requirements/README.md)

## Stack

- Backend: FastAPI + SQLAlchemy + JWT auth
- Frontend: React + Vite + Material UI
- Database: PostgreSQL
- Runtime: Docker Compose

## Quick Start (No Azure Spend)

1. Start services:

```powershell
docker compose up --build
```

2. Open:
- Web app: `http://localhost:5173`
- API docs: `http://localhost:8000/docs`

3. Bootstrap login (created automatically on first API startup):
- Tenant slug: `demo-msp`
- Email: `owner@demo-msp.com`
- Password: `ChangeMe123!`

## Current API Surface

- Auth: `/api/v1/auth/register-owner`, `/api/v1/auth/login`, `/api/v1/auth/me`
- Tenant: `/api/v1/tenants/me`
- Customers: `/api/v1/customers`
- Tickets: `/api/v1/tickets`
- CloudEvents-like ingestion: `/api/v1/events`

## What Is Implemented

- Tenant-aware auth and JWT session flow
- Bootstrap owner creation
- Tenant-scoped customer and ticket CRUD
- Event ingestion with optional ticket auto-creation
- Audit event logging for key actions
- Web UI for login, customer creation, ticket creation, and dashboard counters

## Next Build Focus

- Schema controller and migrations from YAML manifests
- RBAC policy matrix and role admin UI
- Incident/change workflows and SLA timer engine
- AI copilot retrieval and automation policy engine
