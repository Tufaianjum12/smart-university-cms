# Smart University CMS — Phase 2 Database Foundation

This package implements the Phase 2 multi-tenant PostgreSQL database foundation.

## Important
This is a Phase 2 backend package. It was generated separately because the actual Phase 1 project files were not attached/available in the working environment. **Do not overwrite your Phase 1 project blindly.** Merge the files into the existing backend after comparing its current configuration.

## Architecture
- Shared PostgreSQL database.
- Every organization-owned table carries `organization_id`.
- Cross-tenant relationships use composite foreign keys containing `organization_id`.
- Backend tenant context is represented by a ContextVar. Phase 3 will bind it from the authenticated user/session.
- Repository helpers fail closed when tenant context is missing.
- PostgreSQL RLS is intentionally deferred until Phase 3 because there is no authenticated tenant context yet; it is recommended as defense-in-depth after authentication.

## Run
1. Create a PostgreSQL database named `smart_university_cms`.
2. Create `.env` from `.env.example`.
3. Install dependencies: `pip install -r requirements.txt`.
4. Run migrations: `alembic upgrade head`.
5. Seed development data: `python seed_dev.py`.
6. Run tests with a separate database: `set TEST_DATABASE_URL=postgresql+psycopg://.../smart_university_cms_test` on Windows CMD, or `$env:TEST_DATABASE_URL="..."` in PowerShell, then `pytest -q`.

Never run the development seed against production.
