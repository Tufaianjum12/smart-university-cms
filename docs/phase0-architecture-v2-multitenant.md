# Smart University Academic Management System (Smart University CMS)
## PHASE 0 — Architecture & Planning Document (v2 — Multi-Tenant SaaS)

**Status:** Planning only. No implementation code included, per project rules.
**Supersedes:** the original Phase 0 document's single-tenant assumption (Section 4 there evaluated multi-tenancy and deferred it). This version makes multi-tenancy a **foundational, day-one decision**, per your explicit requirement. Everything else from v1 that doesn't depend on tenancy — module list, business-logic formulas, AI/RAG separation principle, testing/security philosophy — is carried forward unchanged and is summarized rather than re-derived here.

---

## 1. Executive Project Vision (updated)

Smart University CMS is now explicitly a **multi-tenant SaaS platform**: a single deployed system that hosts multiple independent educational organizations (universities, colleges, institutes), each with completely isolated academic data, managed centrally by a platform owner (you) who can eventually charge each organization for access.

The two non-negotiable architectural commitments, in priority order:

1. **Tenant isolation is enforced by the backend, structurally — never by frontend hiding, and never by trusting a client-supplied organization ID.** Tenant context is derived only from the authenticated user's server-verified identity.
2. **Deterministic backend logic remains the source of truth for academic numbers** (GPA, CGPA, attendance) — unchanged from v1, and now additionally scoped per-tenant, since grading rules and academic policy (Section 22 in v1) can legitimately differ between organizations.

---

## 2. Product Goals (updated)

1. Host multiple organizations on one platform with **zero data leakage** between them, enforced at the API and data-access layers, not just the UI.
2. Give the platform owner (Super Admin) a control plane to create, configure, suspend, and eventually bill organizations — independent of any single organization's academic data.
3. Give each organization its own admin(s), users, and academic configuration, functioning as if they had a dedicated instance.
4. Keep the academic feature set (Sections 5–22, largely unchanged from v1) correct and trustworthy before layering commercial/billing concerns on top.
5. Architect tenant isolation so it can be strengthened later (schema- or database-per-tenant) for specific large customers, without redesigning the application layer.
6. Defer payment processing entirely — build the multi-tenant *structure* now, billing *logic* later, as you specified.

---

## 3. Target Users (updated)

- **You (Platform Super Admin):** owns the platform, onboards organizations, monitors platform health, will eventually manage billing.
- **Organization Admin** (renamed from v1's "University Admin"): the top administrator within one tenant — a university, college, or institute.
- **Department Admin, Teacher, Student, Parent/Guardian:** unchanged in role from v1, but now every one of them belongs to exactly one organization, and their access is implicitly scoped to it.

---

## 4. Multi-Tenancy Strategy — Evaluation & Recommendation

This is the central architectural decision for v2, so it's addressed first and in depth.

### 4.1 Options evaluated

| Approach | Description |
|---|---|
| **A. Shared database + `tenant_id`** | One PostgreSQL database, one schema, every tenant-owned table carries an `organization_id` foreign key. All queries filter by it. |
| **B. Schema-per-tenant** | One PostgreSQL database, but each organization gets its own schema (e.g., `org_123.students`). |
| **C. Database-per-tenant** | Each organization gets an entirely separate PostgreSQL database (or instance). |

### 4.2 Comparison

| Criterion | A. Shared + tenant_id | B. Schema-per-tenant | C. Database-per-tenant |
|---|---|---|---|
| **Cost** | Lowest — one DB instance regardless of tenant count | Medium — one instance, but schema sprawl complicates connection pooling/migrations | Highest — cost scales linearly with tenant count |
| **Complexity (build)** | Lowest — standard ORM patterns, one migration path | High — dynamic schema switching per request, harder Alembic workflow | High — dynamic connection routing, per-tenant provisioning pipeline |
| **Complexity (operate)** | Low — one thing to monitor, back up, upgrade | Medium-high — N schemas to migrate in lockstep | High — N databases to provision, back up, monitor, upgrade |
| **Security/isolation strength** | Good, but *relies entirely on correct application-layer enforcement* (Section 4.4) | Stronger — a bug in one query can't cross schemas as easily | Strongest — physical separation, a compromised tenant cannot touch another's storage at all |
| **Scalability (many small tenants)** | Excellent — this is exactly what it's designed for | Degrades — Postgres doesn't love thousands of schemas in one DB | Poor — thousands of DB instances is an operational nightmare |
| **Scalability (few large tenants)** | Fine, with the caveat that noisy-neighbor query load is shared | Better isolation of load | Best — a large tenant can be scaled/tuned independently |
| **Maintainability (solo dev)** | Highest — one schema, one Alembic history, one set of models | Lower — every migration must be replayed across all tenant schemas | Lowest — every migration must be applied to every tenant database, and application code needs tenant-aware connection routing |
| **Time-to-first-customer** | Fastest | Slower | Slowest |

### 4.3 Recommendation: **Approach A — shared database with `organization_id`-scoped rows**, for the initial build

This is exactly what your brief anticipated ("initially use a practical shared PostgreSQL database with strong tenant isolation, unless Phase 0 determines another strategy is significantly better") — and nothing in this evaluation overturns that default. For a solo developer building toward a first real customer (Section 3's "Target Users" — a specific department or small college first), Approach A is the only option where build complexity, operational burden, and cost are all simultaneously low. Approaches B and C solve a problem (blast-radius isolation for very large or very sensitive tenants) that you don't have yet, at a cost (migration complexity, connection routing, N× operational surface) you can't currently afford as a solo developer.

**The honest tradeoff being accepted:** Approach A's isolation is *only as strong as the discipline enforcing it* — every single query that touches tenant data must be scoped, with no exceptions. Section 4.4 exists specifically to make that discipline structural instead of a matter of remembering.

### 4.4 How tenant isolation is enforced (not just designed)

The rule from your brief — **"tenant context must be securely determined from the authenticated user/session and cannot simply be trusted from a frontend-supplied organization ID"** — is implemented as a hard architectural constraint, not a convention:

```text
1. JWT issued at login embeds the user's organization_id as a signed
   claim (Phase 3). The frontend never sends organization_id on any
   request — it is derived server-side, every time, from the verified
   token.

2. A FastAPI dependency, get_current_tenant(), extracts and validates
   organization_id from the JWT on every authenticated request. This
   dependency is required by every tenant-scoped router — there is no
   route that reads tenant data without it running first.

3. The repository layer (Section 10) never exposes a raw "get all
   students" query. Every repository method that touches a
   tenant-owned table takes organization_id as a mandatory first
   parameter and applies it as a WHERE clause — structurally, it is
   not possible to call these methods without scoping them.

4. A defense-in-depth second layer: PostgreSQL Row-Level Security (RLS)
   policies on tenant-owned tables, keyed to a session variable
   (SET app.current_org_id) set at the start of each request's
   database session. Even if an application-layer bug ever forgot a
   WHERE clause, RLS would still block the cross-tenant read/write at
   the database level. This is introduced alongside the schema itself
   in Phase 2, not deferred.

5. Platform Super Admin routes are structurally separate — a different
   set of routers/dependencies (get_current_platform_admin()) that
   never resolves or requires an organization_id, and cannot fall
   through into tenant-scoped repository methods.
```

Layers 2 and 3 are enforced by every developer's code having to go through them (you can't accidentally bypass a required function parameter). Layer 4 (RLS) is the safety net for when human discipline fails — cheap to add in Postgres and worth doing from Phase 2, not treated as optional hardening.

### 4.5 Future evolution path

If a specific large customer later requires stronger isolation (e.g., a contractual requirement, a much larger data volume, or a customer sensitive enough to want physical separation), the schema is designed so that a **single tenant's data can be migrated out to its own schema or database** without changing the application code: because every table already carries `organization_id` and every query is already scoped by it, "give tenant X their own database" becomes a data-migration and connection-routing exercise, not an application rewrite. This is explicitly called out as the reason Approach A was chosen over prematurely building B or C.

---

## 5. User Roles & Permissions (RBAC Model, updated for two-plane structure)

Roles now split into **two planes**: the **Platform plane** (you, running the SaaS business) and the **Tenant plane** (each organization's own users). This separation is itself part of the isolation strategy — platform-plane code and tenant-plane code are structurally distinct (Section 4.4, point 5).

### Platform plane

**Super Admin (Platform Owner)**
- **View:** All organizations at a metadata level — name, status, plan, user counts, usage stats. **Not** the academic contents (grades, attendance) of any organization by default.
- **Create/Update:** Organizations, organization status (active/suspended/trial), platform-level configuration, future subscription plans.
- **Delete:** Soft-suspend organizations rather than hard-delete (preserves data for billing disputes, export requests, reactivation).
- **Must NOT:** Casually browse into a specific organization's student grades or attendance without an audit-logged, explicitly justified support action — same principle as v1, now doubly important since this spans customer boundaries.

### Tenant plane (per organization — unchanged in spirit from v1, re-scoped)

**Organization Admin** *(was "University Admin" in v1)*
- Full admin rights within their own organization only: campuses, departments, programs, sessions, academic rule configuration, staff accounts.
- **Must NOT:** see or affect any other organization's existence, configuration, or data — not even know other organizations exist.

**Department Admin, Teacher, Student, Parent/Guardian**
- Identical responsibilities to v1 Section 5, with one addition to every "must NOT" line: **must NOT access data belonging to a different organization**, enforced the same way cross-department access is blocked — via the fine-grained service-layer check, now checking `organization_id` first, before any other scope check.

---

## 6. Complete Feature List (updated)

All v1 features (Section 6 there) carry forward unchanged as **tenant-scoped** features — every one of them now implicitly operates "within an organization." New, additive features for v2:

**Platform/SaaS:** organization registration & onboarding, organization status management (trial/active/suspended), organization-level settings, organization administrators, per-organization user limits, feature/module availability flags, subscription plan definitions (structure only, no billing engine yet), organization-level usage statistics, tenant-specific configuration overrides (e.g., an org's own grading scale, already planned in v1 Section 22 — now explicitly namespaced by `organization_id`).

**Explicitly deferred (per your instruction):** payment processing, billing integration, trial-period enforcement logic, invoicing. The *data model* for subscriptions/plans is designed now (Section 11) so it isn't a schema migration surprise later; the *business logic* for charging money is not built until a dedicated later phase.

---

## 7. MVP vs Advanced Features (updated)

### MVP (multi-tenant from the start)
- Platform Super Admin: create/view/suspend organizations
- Auth issuing tenant-scoped JWTs
- Organization Admin onboarding an organization's own structure (campuses, departments, programs)
- Everything from v1's MVP (course/enrollment, attendance, grades, GPA/CGPA, warnings, timetable, dashboards) — now inherently tenant-scoped, since every table carries `organization_id` from Phase 2 onward
- RLS policies active from Phase 2

### Advanced (unchanged list from v1, plus:)
- Subscription plans with real billing/payment integration
- Trial period automation (auto-suspend on expiry)
- Organization-level usage analytics dashboards
- Self-serve organization signup flow (vs. Super-Admin-provisioned)
- AI assistant, RAG (as in v1 — still gated behind the academic system being correct first)

**Why this order:** multi-tenancy is now structural, so it must be in the MVP (retrofitting `organization_id` onto a schema and every query after the fact is far more dangerous than building it in from Phase 2). Billing is still correctly deferred — it's a business-logic layer on top of an already-tenant-aware system, not a prerequisite for the system to *be* tenant-aware.

---

## 8. System Architecture (updated)

```text
                        React Frontend (Vite)
                                ↓
                     React Router + Axios (JWT)
                                ↓
                         FastAPI Backend
                                ↓
        ┌───────────────────────┼───────────────────────┐
        ↓                       ↓                        ↓
   API Routers            Service Layer             Auth Layer
  (validation)         (business rules,          (JWT issue/verify,
        │                GPA/attendance,          RBAC checks,
        │                 tenant-scoped)          get_current_tenant())
        ↓                       ↓                        ↓
        └───────────────────────┼───────────────────────┘
                                ↓
                    Tenant-Scoped Repository Layer
                (every method requires organization_id)
                                ↓
                       SQLAlchemy ORM Models
                    (organization_id on every
                     tenant-owned table)
                                ↓
                PostgreSQL (shared DB, RLS policies
                     keyed to organization_id)
```

Platform-plane requests (Super Admin managing organizations) take a **separate path**: `Platform API Routers → Platform Service Layer → Platform Repository (organizations table only, no tenant filter needed since it IS the tenant registry) → PostgreSQL`. This path never touches the tenant-scoped repository layer above.

---

## 9. High-Level Module Diagram (updated)

```text
┌─────────────────────────────────────────────────────────────┐
│                         Frontend                                │
│ Platform Admin UI | Org Admin UI | Dashboards | (later) AI Chat │
└─────────────────────────────────────────────────────────────┘
                                ↓ REST (JWT carries organization_id
                                          + role claims)
┌─────────────────────────────────────────────────────────────┐
│                          Backend                                 │
│ ┌─────────────┐                                                 │
│ │  Platform    │  organizations, platform admins, plans          │
│ │   Module     │  (Super Admin only, no tenant filter)           │
│ └─────────────┘                                                 │
│ ┌───────────┐ ┌───────────┐ ┌───────────┐ ┌───────────┐        │
│ │   Auth    │ │Org/Academic│ │ Enrollment│ │Attendance │        │
│ │  Module   │ │  Structure │ │  Module   │ │  Module   │        │
│ └───────────┘ └───────────┘ └───────────┘ └───────────┘        │
│         (all four tenant-scoped: every query carries             │
│                    organization_id)                              │
│ ┌───────────┐ ┌───────────┐ ┌───────────┐ ┌───────────┐        │
│ │Assessment │ │  GPA/CGPA │ │ Timetable │ │Notification│        │
│ │  Module   │ │   Engine   │ │  Module   │ │  Module   │        │
│ └───────────┘ └───────────┘ └───────────┘ └───────────┘        │
│         (tenant-scoped)                                          │
│ ┌───────────┐ ┌───────────┐                                     │
│ │    AI     │ │    RAG    │        (later, tenant-scoped)        │
│ └───────────┘ └───────────┘                                     │
└─────────────────────────────────────────────────────────────┘
                                ↓
                          PostgreSQL
```

---

## 10. Backend Architecture (updated)

Same layered structure as v1 (Section 10 there), with one structural addition:

```text
backend/
├── app/
│   ├── main.py
│   ├── core/                # + tenant.py: get_current_tenant() dependency,
│   │                            get_current_platform_admin() dependency
│   ├── config/
│   ├── db/                  # + RLS session-variable setup on each request
│   ├── models/               # every tenant-owned model inherits a
│   │                            TenantScopedMixin adding organization_id
│   ├── schemas/
│   ├── api/
│   │   ├── v1/                # tenant-scoped routers
│   │   └── platform/            # NEW: Super Admin routers, structurally separate
│   ├── services/
│   ├── repositories/          # every tenant repository method requires
│   │                              organization_id as its first argument
│   ├── auth/
│   └── utils/
```

**Key new responsibility — `core/tenant.py`:** houses `get_current_tenant()`, the FastAPI dependency every tenant-scoped router depends on. It decodes the JWT (via `auth/`), extracts the validated `organization_id` claim, and returns it as a typed object injected into the route function — the route handler never reads `organization_id` from anywhere else (not query params, not request body, not headers). This is the single enforcement point referenced throughout this document.

**`TenantScopedMixin`:** a small SQLAlchemy mixin class every tenant-owned model (students, courses, attendance, etc. — everything except `organizations` itself and platform-level tables) inherits, adding the `organization_id` foreign key and an index on it consistently, rather than each model author remembering to add it by hand.

---

## 11. Database Architecture (updated — Organization as tenant root)

The v1 entity list (Section 11 there) is unchanged in content, with one structural change: **`universities` becomes `organizations`**, sitting at the true root of the hierarchy, and every entity below it in v1's ownership chain gains an `organization_id` column (either directly, or transitively enforced via its parent's `organization_id`, with the direct column still present on frequently-queried tables for simpler, faster tenant-scoped queries and RLS policies).

### New/changed entities

- **organizations** *(new, replaces `universities` as the tenant root)* — PK `id`. Fields: `name`, `slug` (URL-safe identifier), `type` (university/college/institute), `status` (trial/active/suspended), `created_at`. This is the tenant. Every other tenant-owned table's `organization_id` points here.
- **organization_settings** *(new)* — PK `id`, FK `organization_id` (one-to-one). Fields: JSON blob for tenant-specific configuration overrides (grading scale defaults, attendance threshold defaults — the same configurable-rules concept from v1 Section 22, now explicitly namespaced per tenant).
- **subscription_plans** *(new, structure only — no billing logic yet)* — PK `id`. Fields: `name`, `max_users`, `feature_flags` (JSON), `price` (nullable/unused until billing phase). Exists so `organizations.plan_id` has somewhere real to point, without building payment processing now.
- **organization_subscriptions** *(new, structure only)* — PK `id`, FK `organization_id`, FK `subscription_plan_id`. Fields: `status` (trial/active/cancelled), `trial_ends_at`, `started_at`. No payment gateway integration in this phase — this table just gives the future billing phase a place to attach real logic without a schema migration surprise.
- **platform_admins** *(new)* — PK `id`, FK `user_id`. Marks a user as Super Admin, structurally separate from any organization membership.
- **users** *(changed from v1)* — gains `organization_id` (nullable only for `platform_admins`; required for every tenant-plane user). This is the field the JWT claim is minted from at login.
- **campuses, departments, programs, sessions, semesters, sections, classrooms, courses, course_offerings, enrollments, attendance_records, assessments, marks, grades, academic_rules, timetable_entries, notifications, academic_targets, audit_logs** — all unchanged in purpose/fields from v1 Section 11, each now carrying (directly or via `TenantScopedMixin`) an `organization_id` column, indexed, and covered by an RLS policy (Section 4.4).

**Constraint addition:** every unique constraint that was global in v1 (e.g., `courses.code` unique) is now **scoped to `(organization_id, code)`** — two different organizations can both have a course called "CS101" without conflict, which is exactly the kind of bug a forgotten scope would otherwise cause.

---

## 12. Conceptual ERD (updated)

```text
Organization 1─────* Campus 1─────* Department 1─────* Program
     │                                                     │
     │(1)                                                  1
     │                                                      │
     *                                                      *
OrganizationSettings                                    Section ────* Semester
     │
Organization 1────* OrganizationSubscription *────1 SubscriptionPlan
     │
Organization 1────* User (org-scoped users: admins, teachers, students, parents)

PlatformAdmin 1────1 User (org_id = null; separate plane entirely)

[Everything below is scoped by the same Organization via organization_id,
 identical relationships to v1 Section 12:]

Department 1────*Course *────* Course (self, via course_prerequisites)
CourseOffering (Course + Section + Teacher + Semester) *────* Student (via Enrollment)
Enrollment 1────* AttendanceRecord
Enrollment 1────* Marks *────1 Assessment
Enrollment 1────1 Grade
Student *────* Parent (via student_parent_links)
Organization 1────* AcademicRule
Student 1────* AcademicTarget
User 1────* Notification
User 1────* AuditLog
```

**New relationship type of note:** `Organization 1──* everything` is not drawn explicitly at every level because it would clutter the diagram — but it is real and enforced: every box in the second half of this diagram carries an `organization_id` back to the same root `Organization`.

---

## 13. API Architecture (updated)

```text
/api/platform/organizations      # Super Admin only — create/list/suspend orgs
/api/platform/subscriptions        # Super Admin only — plan assignment (no billing yet)

/api/v1/auth                     # login issues a JWT with organization_id + role
/api/v1/users
/api/v1/org-settings              # organization's own configuration
/api/v1/universities → renamed /api/v1/campuses, /departments, /programs
/api/v1/courses
/api/v1/enrollments
/api/v1/attendance
/api/v1/grades
/api/v1/exams
/api/v1/timetable
/api/v1/notifications
/api/v1/academic
```

**Critical rule, stated explicitly because it's the crux of the whole isolation model:** no endpoint under `/api/v1/*` ever accepts `organization_id` as a path parameter, query parameter, or request body field. It is not part of the request contract at all — it is resolved exclusively from the JWT by `get_current_tenant()` (Section 10) on the server. This is the concrete implementation of your instruction that tenant context "cannot simply be trusted from a frontend-supplied organization ID." Endpoints under `/api/platform/*` are the only place `organization_id` appears explicitly in a request, because there a Super Admin is legitimately choosing which organization to act on.

---

## 14. Authentication Architecture (updated)

Same JWT approach as v1 Section 14, with the token payload now explicitly including:

```json
{
  "sub": "<user_id>",
  "organization_id": "<org_id or null for platform admins>",
  "role": "org_admin | department_admin | teacher | student | parent | platform_super_admin",
  "exp": "..."
}
```

`organization_id` is set once, at login, from the authenticated user's own `users.organization_id` — never accepted as login input. A login request only ever supplies credentials; the server looks up which organization (if any) that account belongs to.

---

## 15. Authorization / RBAC Architecture (updated)

Three checks now run in sequence for every tenant-plane request, in this order:

1. **Authenticated?** (valid JWT) — unchanged from v1.
2. **Correct tenant?** (`get_current_tenant()` resolves `organization_id`, and every repository call downstream is scoped to it) — **new, and checked before role**, because a role check without a tenant check is meaningless (a "teacher" role means nothing without knowing *which organization's* teacher).
3. **Correct role/scope within that tenant?** (v1's existing role + ownership checks, Section 15 there) — unchanged, just now operating on an already tenant-filtered dataset.

Platform-plane requests skip steps 2–3 entirely and instead run `get_current_platform_admin()`, a structurally separate dependency (Section 4.4, point 5) that has no concept of `organization_id` scoping.

---

## 16. Business Logic Architecture (updated)

Formulas are **unchanged** from v1 Section 12/16 (attendance %, GPA, CGPA, recovery, target feasibility) — the math doesn't change per tenant. What changes: the **inputs to those formulas** (grading scale, attendance threshold) are now read from `organization_settings`/`academic_rules` scoped to the caller's `organization_id`, not a single global config. Every service function that reads academic rules takes `organization_id` as a parameter, consistent with the repository-layer rule in Section 10.

---

## 17. Notification, AI, and RAG Architecture

**Unchanged in structure from v1** (Sections 13, 14, 15 there) with the same rule applied throughout: every notification, every AI context-assembly step, every RAG document and retrieval is scoped to `organization_id`. Concretely: `notifications.organization_id` (via the owning user), RAG document metadata includes `organization_id` so retrieval never surfaces one organization's policy handbook to another organization's student, and the AI orchestration service (v1 Section 18) receives an already tenant-scoped verified-data context — it never has the ability to query across tenants because the service layer feeding it never can either.

---

## 18. Security Architecture (updated)

All of v1 Section 20's measures carry forward. Added for multi-tenancy:

| Measure | When |
|---|---|
| `organization_id` embedded in JWT, never accepted from client input | Phase 3 (redefined scope — was generic auth, now tenant-aware from the start) |
| `get_current_tenant()` required dependency on every tenant-scoped router | Phase 3 |
| Repository methods structurally require `organization_id` as first parameter | Phase 2 (as soon as any repository exists) |
| PostgreSQL Row-Level Security policies on tenant-owned tables | Phase 2 (alongside schema creation — not deferred) |
| Cross-tenant access attempts logged distinctly in `audit_logs` (e.g., a token from org A somehow referencing an org-B resource ID) | Phase 6+ incrementally, same timeline as v1's general audit logging |
| Platform-plane routes structurally isolated from tenant-plane routes/repositories | Phase 3 (when both planes first exist) |

---

## 19. Configurable Academic Rules (updated)

Unchanged principle from v1 Section 22 (configuration vs. hard-coded), now explicitly **namespaced per organization** via `organization_settings`/`academic_rules.organization_id`. This was already half-designed for this in v1 (rules were always meant to be configurable per-institution); v2 just makes the tenant boundary explicit and enforced rather than implicit.

---

## 20. Development Strategy — Updated Roadmap

The roadmap keeps the same phase count and ordering philosophy as v1, with tenancy folded into the phases where it structurally belongs (not bolted on as separate phases, per your "don't change phases unnecessarily" instruction — this *is* a genuine dependency-driven adjustment, explained below) and one new phase added at the end for billing.

```text
Phase 0  → Planning & Architecture                          [THIS DOCUMENT]
Phase 1  → Project Setup                                     [unchanged scope]
Phase 2  → Database Architecture
             — NOW includes: organizations as tenant root, organization_id
               on every tenant-owned table, RLS policies, subscription_plans/
               organization_subscriptions tables (structure only)
Phase 3  → Authentication & Authorization
             — NOW includes: get_current_tenant(), get_current_platform_admin(),
               organization_id embedded in JWT at login
Phase 4  → Platform + University CMS
             — NOW includes: Super Admin organization CRUD (platform plane)
               alongside Organization Admin's own structure CRUD (tenant plane)
Phase 5  → Course & Enrollment
Phase 6  → Attendance
Phase 7  → Intelligent Attendance Analysis
Phase 8  → Grades & Exams
Phase 9  → GPA / CGPA Engine
Phase 10 → Target GPA / CGPA
Phase 11 → Automatic Warning System
Phase 12 → Timetable
Phase 13 → Smart Class Reminders
Phase 14 → Student Dashboard
Phase 15 → Teacher Dashboard
Phase 16 → Admin Dashboard
             — NOW includes: a Platform Admin dashboard (org list, status,
               usage stats) distinct from the Organization Admin dashboard
Phase 17 → AI Academic Assistant
Phase 18 → RAG
Phase 19 → Security Hardening
             — NOW includes: RLS policy audit, cross-tenant penetration
               testing (attempt to access org B data with an org A token)
Phase 20 → Testing
             — NOW includes: dedicated tenant-isolation test suite (Section 21)
Phase 21 → Docker
Phase 22 → CI/CD
Phase 23 → Initial Production Deployment
Phase 24 → AWS
Phase 25 → Billing & Subscriptions   [NEW — payment processing, trial
             enforcement, invoicing; deliberately last, per your instruction
             to build the academic system correctly first]
```

**Why Phases 2–4 and 16/19/20 absorbed tenancy instead of new phases being inserted:** multi-tenancy isn't a feature bolted onto the academic system — it's a property of *every* table and *every* query. Giving it its own phase would either mean building the schema twice (once without `organization_id`, once with) or building a fake "tenancy phase" with nothing real to test yet, since tenancy only means something once there's data to isolate. The only place a genuinely new phase was needed is Phase 25 (billing), because that's real new functionality with no dependency on earlier phases being redone.

---

## 21. Testing Strategy (updated)

Everything from v1 Section 24 carries forward, plus a new, high-priority category:

**Tenant isolation tests** (Phase 20, but written incrementally alongside each module from Phase 4 onward, the same way authorization tests were in v1): for every tenant-scoped endpoint, an explicit test asserting that a valid, authenticated user from Organization A **cannot** read, list, or modify a resource belonging to Organization B — including by guessing/incrementing IDs. These are treated with the same severity as the GPA calculation tests: a cross-tenant data leak is as disqualifying for a real deployment as a wrong grade.

---

## 22. Scalability Strategy (updated)

Unchanged principles from v1 Section 26, with tenancy-specific notes:
- Every `organization_id` foreign key is indexed from Phase 2 — this is the single most important index in the whole schema, since virtually every query filters on it.
- Composite indexes like `(organization_id, student_id)` are preferred over indexing `organization_id` alone, since almost no query filters by organization alone.
- A "noisy neighbor" org with unusually high query volume is a real risk in the shared-database model (Section 4.2's honest tradeoff) — monitoring per-organization query load becomes relevant once there are several paying tenants, and is the practical trigger for reconsidering Section 4.5's evolution path for that specific tenant.

---

## 23. Data Ownership & Privacy (updated)

Unchanged principles from v1 Section 27, with the tenant boundary now the primary privacy boundary: an organization's data belongs to that organization, and the Super Admin's platform-level access to it is the same "logged, exceptional override" pattern v1 already established for cross-role access — now applied across the additional platform/tenant boundary too.

---

## 24. Major Architectural Decisions (new/updated entries)

**Decision: Shared database + `organization_id`, not schema- or database-per-tenant, for the initial build.**
Why: lowest cost, complexity, and time-to-first-customer while still meeting the "backend-enforced, not frontend-trusted" isolation requirement, via JWT-derived tenant context + mandatory-parameter repositories + RLS as a second layer (Section 4.4).
Alternative: schema-per-tenant or database-per-tenant.
Why not chosen now: both solve a stronger-isolation problem you don't have yet, at an operational cost (N migrations, N connection targets) disproportionate to a solo developer with (initially) a handful of tenants.
Future expansion: Section 4.5 — a specific large tenant can be migrated to its own schema/database later without an application rewrite, because the tenant boundary is already structurally present everywhere.

**Decision: Platform plane and tenant plane are structurally separate code paths, not just role-gated within one path.**
Why: makes it architecturally impossible for a Super Admin route to accidentally fall through into tenant-scoped repository code (and vice versa) — the strongest practical guarantee available short of physically separate services.
Alternative: one set of routes/services, with an `is_platform_admin` boolean check sprinkled into shared tenant logic.
Why not chosen: a single missed `if` check in shared code is exactly the kind of bug that causes cross-tenant leaks; separate code paths remove the possibility structurally rather than relying on vigilance.
Future expansion: if the platform plane grows complex enough (real billing engine, usage analytics service), it's already positioned to be extracted into its own service first, ahead of any tenant-plane module, since it has no tenant-scoped dependencies to disentangle.

**Decision: Row-Level Security (RLS) added in Phase 2, not deferred to Phase 19 hardening.**
Why: RLS is cheap to define alongside the table itself and provides a genuine second enforcement layer beneath application-layer scoping (Section 4.4) — waiting until "hardening" would mean running without it during exactly the phases (2–16) where the schema and query patterns are least battle-tested.
Alternative: rely on application-layer scoping alone until Phase 19.
Why not chosen: contradicts your explicit instruction that isolation "must be enforced at the API/business/data-access layers," and defense-in-depth is inexpensive here relative to the risk being defended against.
Future expansion: none needed structurally — RLS policies are extended automatically as new tenant-owned tables are added, following the same `TenantScopedMixin` pattern.

**Decision: Billing/subscription data model exists from Phase 2 (as empty structure); billing logic is Phase 25.**
Why: adding `organization_id`/`plan_id`/`subscription_status` columns later, after real data exists, is a riskier migration than including them now while tables are still empty; but building Stripe/payment integration now would violate your explicit "academic system first" instruction.
Alternative: add subscription tables only when Phase 25 starts.
Why not chosen: would require a schema migration touching the `organizations` table after it's in real use, for no benefit — the empty structure costs nothing to have early.
Future expansion: Phase 25 fills in real business logic (trial expiry jobs, payment gateway webhooks, invoice generation) against tables that already exist and are already tenant-consistent.

---

## Phase 0 (v2) Completion Checklist

- [x] Three tenancy strategies evaluated against cost/complexity/security/scalability/maintainability, with a clear recommendation and rationale
- [x] Tenant isolation enforcement mechanism specified at JWT, dependency, repository, and database (RLS) layers — not left to frontend trust
- [x] Platform plane vs. tenant plane structurally separated in routing, services, and repositories
- [x] Organization established as the schema's tenant root, with every tenant-owned entity scoped to it
- [x] SaaS-adjacent data model (organizations, settings, plans, subscriptions, platform admins) designed with billing logic explicitly deferred
- [x] RBAC model updated for the two-plane structure
- [x] API contract rule established: `organization_id` is never client-supplied on tenant-scoped routes
- [x] Roadmap updated: tenancy absorbed into Phases 2–4/16/19/20 where it structurally belongs; billing added as new Phase 25
- [x] Testing strategy extended with dedicated tenant-isolation tests
- [x] Decision log updated with the tenancy-strategy decision and its alternatives

---

## Phase 1 Prerequisites (unchanged)

Phase 1 (project setup) has no data model yet, so nothing about this multi-tenancy decision required any change to what was already built there — see the accompanying Phase 1 update below for confirmation and the small documentation-level adjustments made.

---

**End of Phase 0 (v2). Waiting for your explicit instruction: "Start Phase 2."**
