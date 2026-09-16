# Phase 4 — University CMS / Organization Management

Implemented on top of the Phase 3 multi-tenant foundation.

## Scope
- Super Admin organization lifecycle: create/list/get/update/activate/suspend.
- Tenant organization profile and settings.
- Tenant-aware CRUD for campuses, departments, programs, academic sessions, semesters, sections, and classrooms.
- Section `course_id` is optional until the later Course phase.
- Academic sessions support one organization-level `is_current` marker; setting one current session clears the previous current marker.
- Soft archive/deactivation is used for tenant resources instead of physical deletion.
- Composite foreign keys already present in Phase 2 are retained for cross-tenant relationship protection.
- React login, JWT attachment, protected administration routes, role-specific navigation, real API-backed CRUD pages, loading/empty/error feedback, and 401 handling.

## Roles
- `SUPER_ADMIN`: platform organization management.
- `UNIVERSITY_ADMIN`: Phase 4 organization administration.
- `DEPARTMENT_ADMIN`: not granted organization-wide Phase 4 administration because the current Phase 3 user model has no department assignment. This avoids creating an insecure scope workaround. A later user/department association can be integrated without weakening tenant isolation.

## Endpoints
All below are under `/api/v1`.

### Platform
- `POST /organizations`
- `GET /organizations`
- `GET /organizations/{organization_id}`
- `PATCH /organizations/{organization_id}`
- `POST /organizations/{organization_id}/activate`
- `POST /organizations/{organization_id}/suspend`

### Tenant
- `GET/PATCH /organization`
- `GET/PUT /organization/settings`
- `GET/POST /campuses`, `GET/PATCH/DELETE /campuses/{id}`
- `GET/POST /departments`, `GET/PATCH/DELETE /departments/{id}`
- `GET/POST /programs`, `GET/PATCH/DELETE /programs/{id}`
- `GET/POST /academic-sessions`, `GET/PATCH/DELETE /academic-sessions/{id}`
- `GET/POST /semesters`, `GET/PATCH/DELETE /semesters/{id}`
- `GET/POST /sections`, `GET/PATCH/DELETE /sections/{id}`
- `GET/POST /classrooms`, `GET/PATCH/DELETE /classrooms/{id}`

## Migration
```bash
alembic upgrade head
```

## Development accounts
The existing `backend/seed_dev.py` remains the development seed. Its documented development password is `DevPass123!`; do not use these seeded credentials in production.

## Known verification limitation in this build environment
The uploaded project contains a Windows Python virtual environment and Windows/frontend native dependencies. The implementation was syntax-compiled and the Phase 4 unit tests passed in the available Linux runtime. Full PostgreSQL integration tests and Vite production build could not be executed here because the runtime lacks the PostgreSQL `psycopg` package/native frontend Rolldown binding and cannot download packages. Run the migration, integration tests, and frontend build on the normal development machine after dependencies are installed.
