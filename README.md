# Smart University Academic Management System (Smart University CMS)

A modular, **multi-tenant SaaS** academic management platform — organizational
structure, enrollment, attendance, grades, GPA/CGPA tracking, timetables, and
(later) an AI academic assistant grounded in verified backend data. The
platform hosts multiple independent organizations (universities, colleges,
institutes) with backend-enforced data isolation between them.

## Current status

**Phase 1 — Project Setup.** This repository currently contains only the
development foundation: a running React frontend, a running FastAPI backend,
and a verified PostgreSQL connection. There is no authentication and no
academic data model yet — those begin in later phases.

**Architecture note (v2):** the platform is designed as multi-tenant from
Phase 2 onward — one deployment, many organizations, isolated data. Tenant
context is always derived from the authenticated user's JWT on the backend,
never trusted from a frontend-supplied organization ID. See
`docs/phase0-architecture-v2-multitenant.md` for the full rationale,
including the shared-database vs. schema-per-tenant vs. database-per-tenant
evaluation and how isolation is enforced end-to-end.
`docs/phase0-architecture.md` is the original single-tenant v1 document,
kept for reference; v2 supersedes its tenancy section.

Phase 1 required no functional changes for this decision — there's no schema
or auth yet for tenancy to apply to. It becomes real starting in Phase 2
(organizations as the schema's tenant root, Row-Level Security policies) and
Phase 3 (tenant context resolved from the JWT on every request).

## Technology stack

**Frontend:** React, Vite, JavaScript, Bootstrap 5, Bootstrap Icons, React Router, Axios
**Backend:** Python, FastAPI, SQLAlchemy, Alembic, Pydantic
**Database:** PostgreSQL

## Project structure

```text
smart-university-cms/
├── frontend/               React + Vite app
│   ├── src/
│   │   ├── components/      Reusable UI pieces (e.g. StatusDot)
│   │   ├── pages/            Route-level views (e.g. StatusPage)
│   │   ├── layouts/           Shared page shells (e.g. MainLayout)
│   │   ├── routes/             Route definitions
│   │   ├── services/            Axios API calls, one file per backend module
│   │   ├── hooks/                 Data-fetching hooks (e.g. useHealthCheck)
│   │   └── context/                 (reserved for auth state, Phase 3+)
│   └── .env.example
│
├── backend/                FastAPI app
│   ├── app/
│   │   ├── main.py           App factory, CORS, router mounting
│   │   ├── config/            Centralized Settings (env-driven)
│   │   ├── db/                  SQLAlchemy engine/session, connection check
│   │   ├── core/                  Custom exception classes
│   │   ├── api/v1/                  Versioned routers (health.py so far)
│   │   ├── models/                    (empty — academic tables start Phase 2)
│   │   ├── schemas/                     (empty — Pydantic schemas start Phase 2)
│   │   ├── services/                      (empty — business logic starts Phase 2+)
│   │   └── repositories/                    (empty — starts Phase 2+)
│   ├── alembic/              Migration tooling, wired but no migrations yet
│   ├── requirements.txt
│   └── .env.example
│
├── .gitignore
└── README.md
```

## Prerequisites

- Node.js 18+ and npm
- Python 3.11+ (tested with 3.12)
- A running PostgreSQL server (local install, or Docker — Docker itself isn't
  introduced into this project until Phase 21, but you can still run a
  standalone `postgres` container locally if that's easier than a native
  install)

## Backend setup

```bash
cd backend
python -m venv .venv

# macOS / Linux
source .venv/bin/activate
# Windows (PowerShell)
.venv\Scripts\Activate.ps1

pip install -r requirements.txt

cp .env.example .env
# then edit .env: set DATABASE_URL to a real database you've created, e.g.
#   postgresql://postgres:<your-password>@localhost:5432/smart_university_cms
# (create that database first, e.g. `createdb smart_university_cms`)

uvicorn app.main:app --reload
```

Backend now runs at `http://localhost:8000`. Check:

- `http://localhost:8000/` — friendly root message
- `http://localhost:8000/docs` — interactive API docs (Swagger UI)
- `http://localhost:8000/api/v1/health` — real health check, including live
  database connectivity status

## Frontend setup

```bash
cd frontend
npm install
cp .env.example .env
npm run dev
```

Frontend now runs at `http://localhost:5173` and calls the backend's
`/api/v1/health` endpoint on load, displaying the real response.

## Environment variables

**Backend (`backend/.env`, never committed):**

| Variable | Purpose |
|---|---|
| `ENVIRONMENT` | `development` \| `testing` \| `production` |
| `DATABASE_URL` | PostgreSQL connection string |
| `SECRET_KEY` | Reserved for JWT signing, used starting Phase 3 |
| `CORS_ORIGINS` | Comma-separated list of allowed frontend origins |

**Frontend (`frontend/.env`, never committed):**

| Variable | Purpose |
|---|---|
| `VITE_API_BASE_URL` | Base URL of the backend API |

`VITE_`-prefixed variables are baked into the browser bundle at build time and
are publicly visible — they must never contain secrets. Backend secrets
(database password, `SECRET_KEY`, future API keys) live only in
`backend/.env` and are never sent to the frontend.

## What must never be committed

- `backend/.env`, `frontend/.env` (real secrets/config)
- Database passwords, JWT secrets, or any API key, anywhere in source

`.env.example` files (safe placeholders) are committed so the required
variables are documented.

## Roadmap

See the Phase 0 architecture document for the complete 24-phase roadmap.
Phase 2 (Database Architecture) is next, once explicitly requested.
