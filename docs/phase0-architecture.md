# Smart University Academic Management System (Smart University CMS)
## PHASE 0 — Architecture & Planning Document

**Status:** Planning only. No implementation code included, per project rules.
**Prepared for:** Solo developer building a portfolio-grade, production-plausible academic platform.

---

## 1. Executive Project Vision

Smart University CMS is a modular academic management platform that digitizes the core academic lifecycle of a university — organizational structure, enrollment, attendance, grading, GPA/CGPA tracking, timetables, and notifications — and layers an AI assistant and RAG-based knowledge system on top of *verified* backend data.

The defining principle: **deterministic backend logic is the source of truth for all official academic numbers; AI is a reasoning/explanation layer that consumes that truth but never generates it.** This separation is what elevates the project from "student CRUD app" to "credible academic platform architecture," and it will be enforced structurally (Section 14, 16).

The system is designed as a **modular monolith** now, with clean internal boundaries that make future service extraction or multi-tenant SaaS conversion realistic without a rewrite.

---

## 2. Product Goals

1. Provide accurate, auditable academic record-keeping (attendance, grades, GPA/CGPA) with zero tolerance for silent calculation errors.
2. Give every role (student, teacher, admin, parent) a dashboard scoped to exactly the data they're entitled to see.
3. Proactively surface academic risk (low attendance, low CGPA trajectory) via deterministic rules before AI is even introduced.
4. Add an AI assistant later that explains *why* a number is what it is, using retrieved real data — not an AI that guesses or generates numbers.
5. Be deployable today on a lean, low-cost stack (Vercel + Railway) while remaining architecturally compatible with a future AWS migration.
6. Remain a single-organization system in v1, but avoid schema/design decisions that would make multi-tenancy painful later.

---

## 3. Target Users

- **A specific department or small college** as the realistic first deployment target (not a national university chain on day one).
- **Students** who need transparency into attendance, grades, and progress toward degree completion.
- **Teachers** who need to manage attendance and grades for their assigned sections without administrative overhead.
- **Department/University admins** who need oversight, configuration control, and reporting.
- **Parents/guardians** who need read-only visibility into their child's academic standing.
- **You, the developer**, as the primary "customer" for Phase 0–20: this needs to be learnable and explainable as you build it (Rule 5).

---

## 4. User Roles & Permissions (RBAC Model)

Roles form a strict hierarchy for administrative scope, but permissions are **not purely hierarchical** — a University Admin should not automatically see raw student-parent communications, for example. Least privilege applies within each role, not just between roles.

### Super Admin
- **View:** Everything across the platform (if/when multi-tenant, across all organizations).
- **Create/Update/Delete:** Organizations, university admins, global academic-rule templates, system configuration.
- **Must NOT:** Casually browse into individual student grade records without an audit-logged reason — technically capable, but this action should be logged distinctly since it's a privacy-sensitive override.

### University Admin
- **View:** All data within their university — campuses, departments, programs, staff, students, aggregate academic analytics.
- **Create/Update:** Campuses, departments, programs, sessions/semesters, academic rule configuration (grading scale, attendance thresholds), teacher and department-admin accounts.
- **Delete:** Soft-delete only for entities with academic history (never hard-delete a student with grade records — see Section 27).
- **Must NOT:** Directly edit an individual grade a teacher entered without an audit trail entry explaining the override.

### Department Admin
- **View:** All data scoped to their department only — programs, sections, courses, students, teachers within that department.
- **Create/Update:** Course-teacher assignments, section assignments within their department, department-level announcements.
- **Delete:** Same soft-delete constraint as above, scoped to their department.
- **Must NOT:** View or modify data belonging to other departments; must NOT change university-wide academic rules (that's University Admin scope).

### Teacher
- **View:** Only sections/courses they are assigned to teach; only students enrolled in those sections.
- **Create:** Attendance records, marks/grades, assignments, announcements for their own sections.
- **Update:** Attendance and grades they entered, within an allowed correction window (configurable), always logged.
- **Delete:** Generally not allowed on submitted grades — corrections should be new audit-logged entries, not silent deletes.
- **Must NOT:** View other teachers' sections, other students' grades, or any student's data outside their assigned sections; must NOT access GPA/CGPA computation internals across the whole university.

### Student
- **View:** Only their own profile, enrollments, attendance, grades, GPA/CGPA, timetable, notifications, and (later) AI assistant interactions.
- **Create:** Their own AI assistant queries (later phase); assignment submissions (if scoped in later phase).
- **Update:** Limited profile fields (contact info, not academic records).
- **Delete:** Nothing academic.
- **Must NOT:** View any other student's data, raw grading formulas beyond what's configured as transparent, or administrative configuration.

### Parent/Guardian
- **View:** Read-only view of their linked child's attendance, grades, GPA/CGPA, and warnings — nothing else.
- **Create/Update/Delete:** Nothing academic. Possibly their own contact preferences.
- **Must NOT:** Access any data belonging to students they are not linked to; must NOT modify anything academic.

This RBAC model will be implemented via a role field plus fine-grained scope checks (e.g., "teacher owns this section") enforced in the **service layer**, not just at the route/decorator level — decorators check role, service layer checks ownership/scope.

---

## 5. Complete Feature List

**Organization/Academic Structure:** University, Campus, Department, Program, Session, Semester, Section, Classroom management.
**Identity:** Users, Students, Teachers, Parents, Admins, Profiles, Authentication, Authorization.
**Enrollment:** Course catalog, prerequisites, course-teacher assignment, section assignment, student enrollment.
**Attendance:** Recording, percentage calculation, threshold comparison, warning generation, recovery-plan calculation.
**Assessment:** Assignments, quizzes, midterms, finals, projects, marks entry, grade computation.
**Academic performance:** GPA engine, CGPA engine, academic history, failed/improved course handling, target GPA/CGPA planning.
**Timetable:** Class scheduling by section/room/teacher/day/time, conflict detection.
**Notifications:** Rule-triggered academic notifications (attendance, GPA, exams, assignments), announcement broadcasting.
**Dashboards:** Role-specific dashboards with cards, tables, charts.
**AI (later):** Conversational academic assistant grounded in verified data.
**RAG (later):** Policy/handbook document retrieval with citations.
**Platform:** Audit logging, configurable academic rules, security hardening, testing, Docker, CI/CD, deployment.

---

## 6. MVP vs Advanced Features

### MVP (Phases 1–16, roughly)
- Auth + RBAC
- Organization/academic structure CRUD
- Course/enrollment management
- Attendance recording + percentage + recovery calculation
- Grades/exams + GPA/CGPA engine
- Target GPA/CGPA calculator
- Deterministic warning system (attendance, GPA)
- Timetable
- Role-specific dashboards (no AI yet)

### Advanced (Phases 17–24)
- AI academic assistant (explanation layer over verified data)
- RAG over university policy documents
- Advanced analytics (trend charts, cohort comparisons)
- Advanced notification delivery (email/push, not just in-app)
- Multi-tenant conversion (if pursued)
- Advanced audit dashboards
- Docker, CI/CD, cloud scaling, AWS migration

**Why this order:** an academic platform with a shiny AI chatbot but wrong GPA math is worse than useless — it's actively harmful for real users. The MVP must be numerically bulletproof before AI is layered on top of it. This also matches your learning path: relational modeling → business logic → testing discipline, before adding AI/RAG complexity.

---

## 7. System Architecture

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
  (validation,          (business rules,           (JWT issue/verify,
   request/response       GPA/attendance             RBAC checks)
   shaping)                calculations)
        ↓                       ↓                        ↓
        └───────────────────────┼───────────────────────┘
                                ↓
                          Repository Layer
                                ↓
                       SQLAlchemy ORM Models
                                ↓
                           PostgreSQL
```

**Future AI/RAG placement:**

```text
React → FastAPI → Service Layer (fetches verified academic data)
                        ↓
                   AI Orchestration Service
                        ↓
        ┌───────────────┴───────────────┐
        ↓                               ↓
Verified DB Context                RAG Retrieval
(GPA, attendance,                  (policy documents,
 grades — read only,                embeddings, vector DB)
 never AI-generated)
        ↓                               ↓
        └───────────────┬───────────────┘
                        ↓
                  Prompt Assembly
             (explicit boundary: "facts" vs
              "retrieved policy" vs "AI reasoning")
                        ↓
                       LLM
                        ↓
              AI Response (explanation/
              recommendation, labeled as such)
```

The critical architectural rule: **the AI Orchestration Service only ever receives numbers the business-logic layer already computed.** It cannot query the database directly, and it cannot be the origin of an official number shown anywhere in the UI as fact.

---

## 8. High-Level Module Diagram

```text
┌───────────────────────────────────────────────────────────┐
│                         Frontend                             │
│  Auth | Dashboards | Academic UI | Admin UI | (later) AI Chat│
└───────────────────────────────────────────────────────────┘
                                ↓ REST (JWT)
┌───────────────────────────────────────────────────────────┐
│                          Backend                              │
│ ┌───────────┐ ┌───────────┐ ┌───────────┐ ┌───────────┐   │
│ │   Auth    │ │Org/Academic│ │ Enrollment│ │Attendance │   │
│ │  Module   │ │  Structure │ │  Module   │ │  Module   │   │
│ └───────────┘ └───────────┘ └───────────┘ └───────────┘   │
│ ┌───────────┐ ┌───────────┐ ┌───────────┐ ┌───────────┐   │
│ │Assessment │ │  GPA/CGPA │ │ Timetable │ │Notification│   │
│ │  Module   │ │   Engine   │ │  Module   │ │  Module   │   │
│ └───────────┘ └───────────┘ └───────────┘ └───────────┘   │
│ ┌───────────┐ ┌───────────┐                                 │
│ │    AI     │ │    RAG    │        (Phase 17-18, later)     │
│ │  Module   │ │  Module   │                                 │
│ └───────────┘ └───────────┘                                 │
└───────────────────────────────────────────────────────────┘
                                ↓
                          PostgreSQL
```

Each module maps to a Python package under `app/` with its own router, schemas, service, and repository — not literal microservices, but strong internal seams that *could* become services later (Section 26).

---

## 9. Frontend Architecture (React + Vite)

```text
frontend/
├── src/
│   ├── components/        # Reusable, dumb UI components (Button, Card, Table, Badge)
│   ├── pages/              # Route-level views (StudentDashboard, AttendancePage)
│   ├── layouts/             # Shell layouts per role (StudentLayout, AdminLayout)
│   ├── routes/               # Route definitions + ProtectedRoute wrapper
│   ├── services/               # Axios API clients, one file per backend module
│   ├── hooks/                   # useAuth, useAttendance, useGpa, etc.
│   ├── context/                   # AuthContext (user, token, role)
│   ├── utils/                      # formatters, validators, constants
│   └── assets/                      # images, icons
```

- **Pages** belong under `pages/`, one subfolder per role or module (`pages/student/`, `pages/admin/`).
- **Reusable components** (tables, cards, form inputs, status badges) live in `components/`, decoupled from any specific page.
- **API calls** live only in `services/` — pages/components never call `axios` directly; this keeps API contracts in one place and makes backend changes low-blast-radius.
- **Auth state** (JWT, current user, role) lives in `context/AuthContext`, exposed via a `useAuth` hook.
- **Protected/role-based routes** live in `routes/`, using a `ProtectedRoute` component that checks `useAuth().role` against an allowed-roles list per route.
- **Role-based UI logic** (e.g., "show this button only to teachers") stays close to the component that renders it, driven by the `useAuth` hook — not scattered ad hoc `if` checks across pages.
- **Custom hooks** wrap `services/` calls with loading/error state so pages stay declarative.

**Redux:** not justified yet. Auth state + a handful of API-driven page states are well handled by React Context + local component state. Redux would be revisited only if cross-cutting client state (e.g., a complex multi-step enrollment wizard spanning many pages) becomes hard to manage with Context alone — that's a "later, if needed" decision, not a default.

---

## 10. Backend Architecture (FastAPI)

```text
backend/
├── app/
│   ├── main.py              # App factory, router registration, middleware
│   ├── core/                 # Settings, security utils (hashing, JWT), exceptions
│   ├── config/                 # Environment-based config classes
│   ├── db/                       # Engine, session, base model, Alembic hookup
│   ├── models/                     # SQLAlchemy ORM models, one file per domain
│   ├── schemas/                     # Pydantic request/response schemas
│   ├── api/                          # Routers, grouped by module (api/v1/attendance.py)
│   ├── services/                       # Business logic (GPA calc, attendance recovery)
│   ├── repositories/                    # DB query layer, isolates SQLAlchemy from services
│   ├── auth/                              # JWT issuance, dependency-injected auth guards
│   └── utils/                               # Shared helpers (date math, pagination)
├── tests/
├── alembic/
├── requirements.txt
└── .env
```

**Responsibilities:**
- **`api/` (routers):** HTTP concerns only — parse request, call a service, shape the response. No business logic here.
- **`schemas/`:** Pydantic models define the exact request/response contract; never expose ORM models directly to the API layer.
- **`models/`:** SQLAlchemy ORM classes representing tables and relationships. No business logic here either — just structure and constraints.
- **`services/`:** Where GPA, CGPA, attendance percentage, and recovery-plan logic actually lives. Pure, testable functions/classes that take data in and return results — this is what Section 24's tests target directly.
- **`repositories/`:** Encapsulate SQLAlchemy queries so services don't write raw queries inline; makes swapping query strategies or adding caching easier later.
- **`auth/`:** Password hashing (bcrypt/argon2), JWT creation/validation, `get_current_user` and `require_role(...)` FastAPI dependencies.
- **Database session:** a per-request session via FastAPI dependency injection (`Depends(get_db)`), committed/rolled back at the request boundary.
- **Configuration:** a Pydantic `Settings` class reading from environment variables, with distinct behavior per environment (Section 23).
- **Error handling:** a small set of custom exception classes (e.g., `NotFoundError`, `PermissionDeniedError`) caught by global FastAPI exception handlers and translated into consistent JSON error responses.
- **Logging:** structured logging (not print statements) from day one, even if it just goes to stdout initially — this makes Section 17's audit logging a natural extension rather than a retrofit.
- **Testing:** `tests/` mirrors `app/` structure; service-layer tests are the highest priority (Section 24).

---

## 11. Database Architecture (Conceptual)

For each entity: purpose, key fields, and relationships. (Final SQL/DDL is explicitly deferred — Section 10 of your brief — this is model *design*, not implementation.)

- **users** — Base identity table. PK `id`. Fields: email, hashed_password, role, is_active, created_at. One-to-one with `students`, `teachers`, `parents`, or `administrators` depending on role (a "base + role-specific extension" pattern, avoiding one giant table with mostly-null columns).
- **universities** — PK `id`. Fields: name, code, settings (JSON for academic-rule defaults). This is also the natural seam for a future `organization_id` if multi-tenancy is adopted (Section 4/12).
- **campuses** — PK `id`, FK `university_id`. Fields: name, address.
- **departments** — PK `id`, FK `campus_id`. Fields: name, code.
- **programs** — PK `id`, FK `department_id`. Fields: name, degree_level, total_credit_hours.
- **academic_sessions** — PK `id`, FK `university_id`. Fields: name (e.g. "2026-2027"), start_date, end_date.
- **semesters** — PK `id`, FK `academic_session_id`. Fields: name, start_date, end_date.
- **sections** — PK `id`, FK `program_id`, FK `semester_id`. Fields: name/code, capacity.
- **classrooms** — PK `id`, FK `campus_id`. Fields: room_number, capacity.
- **courses** — PK `id`, FK `department_id`. Fields: code, title, credit_hours. Many-to-many to itself via `course_prerequisites` junction table (`course_id`, `prerequisite_course_id`).
- **teachers** — PK `id`, FK `user_id`, FK `department_id`.
- **students** — PK `id`, FK `user_id`, FK `program_id`. Fields: roll_number, admission_date.
- **parents** — PK `id`, FK `user_id`. Many-to-many to `students` via `student_parent_links` (a parent may have multiple children; a student may have multiple guardians).
- **course_offerings** — PK `id`, FK `course_id`, FK `section_id`, FK `teacher_id`, FK `semester_id`. Represents "this course, taught by this teacher, in this section, this semester" — the real-world unit students enroll into.
- **enrollments** — PK `id`, FK `student_id`, FK `course_offering_id`. The junction resolving the many-to-many between students and course_offerings. Fields: enrollment_date, status (active/dropped/completed).
- **attendance_records** — PK `id`, FK `enrollment_id`, FK `class_session_id` (or date). Fields: status (present/absent/late), recorded_by, recorded_at.
- **assessments** — PK `id`, FK `course_offering_id`. Fields: type (quiz/midterm/final/assignment/project), max_marks, weight_percentage.
- **marks** — PK `id`, FK `assessment_id`, FK `enrollment_id`. Fields: obtained_marks, graded_by, graded_at.
- **grades** — PK `id`, FK `enrollment_id`. Fields: final_grade_letter, grade_point, computed_at. This is a *derived/cached* result of the GPA service, not user-entered directly (Section 12).
- **academic_rules** — PK `id`, FK `university_id`. Fields: min_attendance_percent, grading_scale (JSON), gpa_policy (JSON) — the configuration table referenced in Section 22.
- **timetable_entries** — PK `id`, FK `course_offering_id`, FK `classroom_id`. Fields: day_of_week, start_time, end_time.
- **notifications** — PK `id`, FK `user_id`. Fields: type, message, is_read, created_at, related_entity (polymorphic reference, e.g. which enrollment triggered it).
- **academic_targets** — PK `id`, FK `student_id`. Fields: target_cgpa, target_date, created_at — supports Section 12's "target CGPA" feature.
- **audit_logs** — PK `id`, FK `user_id` (actor), fields: action, entity_type, entity_id, before_state (JSON), after_state (JSON), timestamp (Section 17).

**Constraints of note:** unique `(student_id, course_offering_id)` on `enrollments` to prevent duplicate enrollment; unique `(email)` on `users`; check constraints on percentage/GPA ranges; soft-delete columns (`is_active` / `deleted_at`) instead of hard deletes on any table with academic history.

---

## 12. Conceptual ERD

```text
University 1─────* Campus 1─────* Department 1─────* Program
                                                          │
                                                          1
                                                          │
                                                          *
                                                       Section ────* Semester
                                                          │
Department 1────*Course *────* Course (self, via course_prerequisites)
     │
     1
     │
     *
CourseOffering (Course + Section + Teacher + Semester) *────* Student
                     │                                        (via Enrollment)
                     │
                   Teacher

Student 1────* Enrollment *────1 CourseOffering
Enrollment 1────* AttendanceRecord
Enrollment 1────* Marks *────1 Assessment
Enrollment 1────1 Grade   (derived)

Student *────* Parent   (via student_parent_links)
University 1────* AcademicRule
Student 1────* AcademicTarget
User 1────* Notification
User 1────* AuditLog (as actor)
```

**Relationship types:**
- **One-to-one:** `users` ↔ role-specific tables (`students`, `teachers`, `parents`, `administrators`) — each user row extends into exactly one role table.
- **One-to-many:** University→Campus→Department→Program→Section (strict hierarchy); Enrollment→AttendanceRecord; Assessment→Marks.
- **Many-to-many, resolved via junction tables:** Student↔CourseOffering (via `enrollments`), Student↔Parent (via `student_parent_links`), Course↔Course prerequisites (via `course_prerequisites`).

---

## 13. API Architecture

```text
/api/v1/auth              # login, refresh, logout
/api/v1/users              # user profile CRUD (admin-scoped)
/api/v1/universities         # university/campus/department/program CRUD
/api/v1/programs
/api/v1/courses               # course + prerequisite management
/api/v1/course-offerings        # course+section+teacher+semester combos
/api/v1/enrollments               # student enrollment actions
/api/v1/attendance                  # record + query attendance, recovery calc
/api/v1/assessments                   # assignment/exam definitions
/api/v1/marks                           # marks entry, scoped to teacher's offerings
/api/v1/grades                            # computed grade retrieval
/api/v1/academic                            # GPA/CGPA, target planning
/api/v1/timetable
/api/v1/notifications
/api/v1/audit-logs                             # admin-only
```

- **Versioning:** URL-based (`/api/v1/...`) from day one — cheap insurance, avoids breaking early frontend/backend contract changes from becoming a crisis.
- **Resource naming:** plural nouns, REST verbs (GET/POST/PATCH/DELETE) mapped to standard CRUD; calculation endpoints (e.g., attendance recovery) are modeled as `GET /attendance/{enrollment_id}/recovery-plan` — a computed *resource*, not an RPC-style verb in the URL.
- **Auth:** JWT bearer token in `Authorization` header; `get_current_user` dependency extracts and validates it.
- **Authorization:** `require_role([...])` dependency for coarse role checks; explicit ownership/scope checks inside services for fine-grained checks (a teacher can only touch their own offerings).
- **Request validation:** Pydantic schemas on every request body; FastAPI auto-generates 422 errors for invalid input.
- **Response schemas:** explicit Pydantic response models — never return raw ORM objects.
- **Error responses:** consistent shape, e.g. `{"detail": "...", "error_code": "..."}`, via global exception handlers.
- **Pagination:** `?page=&page_size=` or cursor-based for large lists (student rosters, attendance history), decided per-endpoint based on expected volume.
- **Filtering/sorting:** query params (`?status=active&sort=name`), validated against an allow-list per endpoint to avoid arbitrary query injection.

---

## 14. Authentication Architecture

- Passwords hashed with **bcrypt** (or argon2) — never stored plaintext, never logged.
- **JWT access tokens**, short-lived (e.g., 15–30 min), containing `user_id`, `role`, and minimal claims — not sensitive academic data.
- **Refresh token strategy:** a longer-lived refresh token (e.g., 7 days), stored httpOnly if/when cookies are introduced, or held client-side with rotation if kept simple initially. Given solo-dev complexity budget, MVP can start with access-token-only + re-login on expiry, and refresh tokens can be added as a Phase 3 stretch goal once basic auth is solid — this is a case where "smallest reasonable thing first" applies.
- Token validation happens via a FastAPI dependency (`get_current_user`) injected into every protected route.
- Logout is primarily client-side (token discard); server-side token revocation/blacklisting is a "later" hardening item (Section 16) once refresh tokens exist.

---

## 15. Authorization / RBAC Architecture

Two layers, deliberately kept separate:

1. **Coarse-grained (route level):** a `require_role(["teacher", "department_admin"])` FastAPI dependency rejects requests before they reach business logic.
2. **Fine-grained (service level):** given a role passed the coarse check, the service layer verifies *ownership/scope* — e.g., "is this teacher actually assigned to this course_offering?" "is this parent actually linked to this student?" This is where most real-world data leaks happen if skipped, so it's treated as mandatory, not optional polish.

This mirrors Section 4's RBAC table directly — every "must NOT" line becomes a concrete service-layer check.

---

## 16. Business Logic Architecture

Deterministic, backend-only, unit-tested logic — never delegated to an LLM.

```text
attendance_percentage = present_classes / total_classes × 100

grade_point = f(marks_obtained, academic_rules.grading_scale)
gpa = Σ(grade_point × credit_hours) / Σ(credit_hours)   [per semester]
cgpa = Σ(grade_point × credit_hours) / Σ(credit_hours)  [across all completed semesters,
                                                           respecting improvement/repeat policy]

attendance_recovery:
  given current present/total and a required threshold,
  solve for minimum additional consecutive "present" classes N such that
  (present + N) / (total + N) ≥ threshold

target_cgpa_feasibility:
  given current_cgpa, completed_credits, target_cgpa, remaining_credits,
  compute required_future_gpa = 
     (target_cgpa × (completed_credits + remaining_credits) − current_cgpa × completed_credits)
     / remaining_credits
  flag as infeasible if required_future_gpa exceeds the grading scale's maximum.
```

All of this lives in `services/`, is unit-testable with no HTTP or DB dependency where possible (pure functions taking numbers in, returning numbers out), and is the **only** legitimate source for any GPA/CGPA/attendance number shown anywhere in the product — including inside AI responses later.

---

## 17. Notification Architecture

- **Triggers:** attendance drop below threshold, failed course, low marks, GPA below target, academic probation, missing assignment, upcoming exam/class, announcements.
- **Generation strategy:** a hybrid —
  - *Immediate* triggers (e.g., a teacher just submitted a failing grade) generate a notification synchronously as part of that request's service logic.
  - *Scheduled* triggers (e.g., "attendance dropped below threshold as of last night's data," "exam in 3 days") run via a periodic job (initially a simple scheduled script/cron, later something like APScheduler or a task queue if volume grows) — deliberately not built as a heavy job-queue system in the MVP.
- **Storage:** all notifications persisted in PostgreSQL (`notifications` table) regardless of delivery channel, so the frontend always has a reliable in-app inbox even before email/push exists.
- **Delivery:** in-app (MVP) first; email/push are explicitly "later" (Advanced tier, Section 6) — they're a delivery-channel add-on, not a redesign.

---

## 18. AI Architecture

The core guarantee: **the AI cannot originate an official academic fact.**

Enforcement mechanism:
1. When a student asks "why is my GPA low," the API request hits a normal authenticated, authorized endpoint.
2. The **service layer** (same GPA/attendance services from Section 16) computes or retrieves the real numbers first.
3. Those numbers are assembled into a structured, clearly-labeled **context object** — e.g., `{"verified_data": {...}, "retrieved_policy_snippets": [...]}`.
4. This context is injected into the LLM prompt with explicit instructions and structural separation: "The following are verified facts, treat them as ground truth and do not alter them. The following are policy excerpts, cite them. Your role is to explain and recommend, not to state new numeric facts."
5. The AI's output is tagged in the UI as an **explanation/recommendation**, visually distinct from the **verified data** it's explaining (e.g., the GPA number itself always renders from the database value, never from the AI's text).

This means the "AI service" is architecturally a *consumer* of the business-logic layer, with no direct database access and no authority to write back academic records.

---

## 19. RAG Architecture

```text
Policy Documents (PDF/DOCX: attendance policy, grading policy, handbook, etc.)
        ↓
Text Extraction
        ↓
Chunking (semantic or fixed-size with overlap)
        ↓
Embeddings (via an embedding model/API)
        ↓
Vector Database (e.g., pgvector inside the existing PostgreSQL, or a
                  dedicated vector store — evaluated in Phase 18)
        ↓
Retrieval (top-k similarity search, filtered by university/document metadata)
        ↓
Relevant Context + Source Citations
        ↓
LLM (combined with verified academic data context from Section 18)
        ↓
Answer, with citations back to the source document/section
```

- **Ingestion:** an admin-facing upload flow (later phase) that extracts text, chunks, embeds, and stores with metadata (`document_type`, `university_id`, `version`, `effective_date`).
- **Metadata** enables scoping retrieval to the right university/document version and enables citation display.
- **Hallucination prevention:** the LLM is instructed to answer only from retrieved chunks for policy questions, and the UI surfaces the source chunk/citation so a student can verify it — the same "don't blindly trust AI text" principle as Section 18.
- **Versioning:** policy documents are versioned; retrieval defaults to the currently-effective version, with old versions retained for audit purposes.

Using **pgvector** (a PostgreSQL extension) rather than introducing a separate vector database is the leading candidate for Phase 18, since it avoids adding new infrastructure for what will likely be a modest document corpus — a dedicated vector DB would only be justified if corpus size or query volume later demands it (see Section 36 decision log entry).

---

## 20. Security Architecture

| Measure | When |
|---|---|
| Password hashing (bcrypt/argon2) | Phase 3 (early) |
| JWT auth, role-based route guards | Phase 3 (early) |
| Input validation via Pydantic | Phase 3 onward, every endpoint |
| SQL injection prevention (parameterized queries via SQLAlchemy ORM, no raw string SQL) | From day one, structural |
| CORS restricted to known frontend origin(s) | Phase 3 (early), tightened per environment |
| Environment variables for all secrets, `.env` never committed | Phase 1 (immediate) |
| Secret management (Railway/Vercel env vars in prod) | Phase 23 (deployment) |
| Rate limiting (e.g., on `/auth/login`) | Phase 19 (hardening), though a lightweight version on login is reasonable earlier |
| Centralized error handling (no stack traces leaked to client) | Phase 3 onward |
| Structured logging | Phase 1 onward |
| Sensitive data protection (no plaintext passwords/tokens in logs) | Structural, from day one |
| Authorization scope checks (Section 15) preventing cross-student data access | Phase 3 onward, tested continuously |
| API abuse protections (rate limiting, payload size limits) | Phase 19 |
| Audit logging | Phase 6+ incrementally, formalized Phase 19 |

**Never exposed to frontend or committed to GitHub:** database password, JWT secret, LLM API key — enforced via `.env` + `.gitignore` from Phase 1, and via platform-level environment variable injection in deployment (Phase 23).

---

## 21. Audit Logging Strategy

**Should be logged** (write-once, append-only `audit_logs` table):
- Teacher changes to attendance or grades (before/after values).
- Admin changes to student information.
- Grade submissions.
- Changes to academic rules/configuration.
- Logins (success/failure) and password changes.
- Any Super Admin access to individual student records (Section 4).

**Why:** academic records carry real consequences (a wrong grade, a disputed attendance mark); an append-only audit trail is the mechanism that makes disputes resolvable and makes the system trustworthy enough to actually deploy at an institution. It also directly supports Section 27 (data ownership/privacy) by making "who accessed what, when" answerable.

Not implemented in Phase 0 — this is a design commitment carried into Phase 6 (attendance) onward, where the first mutating actions appear.

---

## 22. Configurable Academic Rules

**Database/config-driven** (varies by institution): minimum attendance percentage, grading scale (letter-to-point mapping and boundaries), GPA/CGPA calculation policy (e.g., whether repeated courses replace or average), academic probation thresholds, improvement-attempt policies.

**Hard-coded** (structural, not policy): the *shape* of the calculation (e.g., "GPA = Σ(grade_point × credit_hours) / Σ(credit_hours)" as a formula pattern), the existence of the attendance/GPA concepts themselves, RBAC role definitions.

This distinction is what the `academic_rules` table (Section 11) exists for — it stores the *numbers and mappings*, while the `services/` layer contains the *formula structure* that consumes them. This is also what makes future multi-university support realistic without duplicating code per university.

---

## 23. Git/GitHub Workflow

Simplest professional workflow suitable for a solo developer:

```text
main        ← always deployable
  └── feature/attendance-system
  └── feature/gpa-engine
  └── feature/authentication
```

- **No `develop` branch** for a solo dev — an extra long-lived branch adds merge overhead without a team to justify it; `main` + short-lived feature branches is enough. (This is a deliberate deviation from the brief's example diagram, explained per Rule: a `develop` branch earns its keep with a team doing parallel release trains, not with one developer merging sequentially.)
- **Feature branches** named `feature/<short-description>`, one per phase or sub-feature, merged via self-reviewed PRs (even solo, PRs create a record and force a diff review).
- **Commit conventions:** Conventional Commits style (`feat:`, `fix:`, `refactor:`, `test:`, `docs:`) — cheap, greppable history.
- **`.gitignore`:** `.env`, `node_modules/`, `__pycache__/`, `venv/`, build artifacts.
- **`.env.example`** committed (no real secrets) so the setup process is documented.
- **README:** setup instructions, architecture summary, phase status.
- **Issue tracking:** GitHub Issues mapped loosely to phases/sub-features — not mandatory process, just a backlog.
- **Releases/tags:** tag `v0.1.0` etc. at the end of major phases (e.g., after Phase 16 MVP complete) for a clean rollback point.

---

## 24. Environment Strategy

```text
Development   → local Postgres, local FastAPI/Vite, verbose logging, permissive CORS
Testing       → separate test database, seeded/reset per test run, mocked external calls (LLM)
Production    → Railway Postgres, restricted CORS, minimal logging verbosity, secrets from platform env vars
```

- **`.env`**: real local values, **never committed**.
- **`.env.example`**: documents every required variable with placeholder values, committed.
- **Never committed:** `DATABASE_URL` with real credentials, `JWT_SECRET`, any LLM API key, any third-party credential.
- Config loaded via a Pydantic `Settings` class that reads environment variables and validates presence/type at startup — the app should fail fast and loudly if a required secret is missing, not silently misbehave.

---

## 25. Testing Strategy

### Backend
- **Unit tests** on every service-layer function, especially GPA/CGPA/attendance/recovery calculations — these get the highest test density in the whole project, with edge cases (zero credit hours, zero total classes, already-above-target scenarios, boundary percentages) explicitly covered.
- **API tests** (FastAPI `TestClient`) for each router — status codes, response shapes, validation errors.
- **Authentication tests:** login success/failure, token expiry handling.
- **Authorization tests:** explicit tests asserting a teacher *cannot* access another teacher's section, a student *cannot* access another student's grades, etc. — these directly test the Section 15 fine-grained checks and should be treated as seriously as the calculation tests.

### Frontend
- Component tests for critical interactive pieces (forms, dashboards rendering role-correct data) using a lightweight framework (e.g., Vitest + React Testing Library) — not exhaustive coverage, but enough to catch regressions in role-conditional rendering.
- UI behavior tests for protected routing (unauthenticated/wrong-role users are redirected correctly).

**Why this prevents incorrect academic calculations:** because the calculation logic is isolated in pure, dependency-light service functions (Section 16), it can be tested with dozens of numeric edge cases cheaply and run on every commit — making a wrong GPA formula a caught bug, not a shipped one.

---

## 26. Docker Strategy (Later — Phase 21)

- One `Dockerfile` for the FastAPI backend, one for the React frontend (or a static build served separately).
- `docker-compose.yml` for local dev: backend + frontend + PostgreSQL, so a fresh clone can run with one command.
- Not needed for early phases — local Python venv + local Postgres is faster to iterate on while the schema is still changing rapidly. Docker earns its place once the stack stabilizes and reproducibility across machines/environments starts to matter (Phase 21, deliberately after the MVP is functionally complete).

---

## 27. CI/CD Strategy (Later — Phase 22)

- GitHub Actions pipeline: on PR → run backend tests + frontend tests + lint; on merge to `main` → optionally trigger deployment (Vercel/Railway both support git-push deploys natively, reducing how much CI/CD you need to hand-build).
- Kept deliberately simple for a solo project: test-and-lint gate on PRs, auto-deploy on merge to `main`. No complex multi-stage pipelines until there's a real reason (e.g., a staging environment requirement).

---

## 28. Initial Deployment Architecture

```text
User
 ↓
Vercel (React static build, CDN-served)
 ↓  (HTTPS API calls)
Railway (FastAPI backend, containerized)
 ↓
Railway Managed PostgreSQL
```

- **Frontend deployment:** Vercel, connected to the GitHub repo, auto-deploys `main`.
- **Backend deployment:** Railway, running the FastAPI app (via its own build/Docker support), auto-deploys `main`.
- **Database:** Railway managed PostgreSQL, with connection string injected as an environment variable — never hard-coded.
- **CORS:** backend restricts allowed origins to the deployed Vercel URL(s) + localhost for dev.
- **Production API URL:** frontend reads the backend URL from a build-time environment variable, not hard-coded.
- **Domain/HTTPS:** both Vercel and Railway provide HTTPS by default; a custom domain can be attached later.
- **Logs:** platform-provided logs (Railway/Vercel dashboards) suffice initially; a dedicated log aggregator is a "later, if needed" item.
- **Backups:** Railway's managed Postgres backup features initially; explicit backup policy documented before any real student data is entered.
- **Migrations:** Alembic migrations run as part of the deploy step (or manually pre-deploy initially), never `create_all()`-style schema sync in production.
- **Monitoring:** basic uptime/error monitoring (e.g., a free-tier tool) added once the app is live; full observability stack is an AWS-era concern.

---

## 29. Future AWS Architecture

When/if migration is warranted (real institutional adoption, cost, or control requirements):

```text
Route 53 (DNS) → CloudFront (CDN) → S3 (React static build)
                                          ↓
                         API Gateway / ALB → ECS/Fargate (FastAPI containers)
                                          ↓
                              RDS PostgreSQL (Multi-AZ)
                                          ↓
                          S3 (documents for RAG) + OpenSearch/pgvector
                                          ↓
                          CloudWatch (logs/monitoring) + Secrets Manager
```

This is explicitly a **later** architecture — the Railway/Vercel setup is fully capable of running a real single-institution deployment; AWS migration is justified by scale, compliance, or cost inflection points, not adopted preemptively (Section 3's "avoid unnecessary technology" principle applies here directly).

---

## 30. Scalability Strategy

Growth path: 1 university/100 students → many organizations/thousands of students.

- **Indexing:** foreign keys and frequently-filtered columns (e.g., `enrollments.student_id`, `attendance_records.enrollment_id`, `users.email`) indexed from the start — cheap now, expensive to retrofit under load.
- **Pagination:** applied to every list endpoint from the MVP (Section 13) so it's never an emergency fix later.
- **Query optimization:** rely on the repository layer to avoid N+1 queries (use SQLAlchemy eager loading where relationships are always needed together, e.g., enrollment + student + course_offering for a roster view).
- **Caching:** not needed at MVP scale; a read-through cache (e.g., Redis) for computed dashboards/analytics becomes reasonable once query load actually shows it (avoid premature caching — it's a correctness risk for numbers that must stay accurate).
- **Background jobs:** the notification scheduler (Section 17) is the first background-job need; a simple cron/APScheduler suffices well past 1 university, thousands of students — a full task queue (Celery/RQ) is a later-scale concern.
- **API scalability:** stateless FastAPI instances behind Railway's/AWS's load balancing scale horizontally without architecture changes, because JWT auth means no server-side session state.
- **File storage:** RAG documents and any future file uploads (assignment submissions) belong in object storage (S3 or equivalent), not the database, from whenever file upload is introduced.
- **Logging/monitoring:** scale from platform logs → structured centralized logging → full observability stack roughly in step with the deployment tier (Railway → AWS).

---

## 31. Data Ownership & Privacy

- **Ownership:** academic records conceptually belong to the university/institution deploying the system; students have a right to view their own data (enforced by RBAC, Section 4/15).
- **Access:** strictly governed by the RBAC model; every access to another person's academic data is either role-justified (teacher viewing their own section) or explicitly audit-logged (admin override, Section 21).
- **Data isolation:** enforced at the service layer via ownership checks now; would become row-level `organization_id` filtering if multi-tenancy is adopted (Section 4).
- **Backups:** covered under Section 28's deployment backup policy; backup contents are as sensitive as production data and must be handled with equal access controls.
- **Deletion policies:** soft-delete by default for anything with academic history (Section 11); hard deletion (e.g., for a legitimate erasure request) is a deliberate, admin-only, audit-logged operation — not a default `DELETE` endpoint.
- **Audit trails:** Section 21.
- **Privacy considerations:** minimize what's stored (no unnecessary PII beyond what's needed for academic administration), and treat AI/LLM API calls as a data-egress point — verified academic data sent to an LLM provider is a privacy-relevant design decision that should be explicitly reviewed before Phase 17, not assumed safe by default.

**Compliance disclaimer:** no claim of compliance with any specific jurisdiction's data protection law (e.g., FERPA, GDPR) is made at this stage — that requires dedicated legal/compliance review before any real student data is processed, which is out of scope for Phase 0 but flagged here so it isn't forgotten before a real deployment.

---

## 32. Complete Phase Roadmap (Unchanged from Your Brief)

```text
Phase 0  → Planning & Architecture                 [THIS DOCUMENT]
Phase 1  → Project Setup
Phase 2  → Database Architecture (schema/DDL, Alembic)
Phase 3  → Authentication & Authorization
Phase 4  → University CMS (org structure CRUD)
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
Phase 17 → AI Academic Assistant
Phase 18 → RAG
Phase 19 → Security Hardening
Phase 20 → Testing
Phase 21 → Docker
Phase 22 → CI/CD
Phase 23 → Initial Production Deployment
Phase 24 → AWS
```

---

## 33. Dependencies Between Phases

- Phase 2 (DB schema) depends on this document's Section 11/12 model being stable — schema churn after Phase 2 should be minimized.
- Phase 3 (Auth) depends on Phase 2's `users` table existing.
- Phases 4–6 (org structure, enrollment, attendance) depend on Phase 3's RBAC guards being in place, since every endpoint from here on is role-scoped.
- Phase 7 (intelligent attendance analysis) depends on Phase 6's raw attendance data model and directly implements Section 16's recovery-calculation formula.
- Phase 8 (grades/exams) depends on Phase 5 (enrollment) and Phase 3 (auth/RBAC for teacher scoping).
- Phase 9 (GPA/CGPA engine) depends on Phase 8's grade data and Section 22's configurable `academic_rules` table.
- Phase 10 (target GPA/CGPA) depends on Phase 9's engine being correct and tested.
- Phase 11 (warning system) depends on Phase 7 and Phase 9/10 both existing, since warnings are triggered by their outputs.
- Phase 12 (timetable) is largely independent and could be reordered earlier if desired, but follows enrollment logically since timetables reference course_offerings.
- Phases 14–16 (dashboards) depend on essentially everything before them being functional, since dashboards are read-aggregations of prior modules.
- Phase 17 (AI) strictly depends on Phases 7–11 being correct and tested — AI explains numbers that must already be trustworthy (Section 14/18's core principle).
- Phase 18 (RAG) is independent of the academic modules but depends on Phase 19-level security awareness for document access control.
- Phase 19 (security hardening) formalizes practices that should already exist informally from Phase 3 onward — it's a hardening pass, not a first introduction.
- Phase 20 (testing) should really be continuous from Phase 3 onward (Section 25), with Phase 20 as a dedicated coverage/gap-filling pass before deployment.
- Phases 21–24 (Docker/CI-CD/deploy/AWS) depend on the application being functionally complete and reasonably tested.

---

## 34. What You'll Need to Learn Before Each Major Phase

- **Before Phase 2:** relational modeling fundamentals, normalization, SQLAlchemy ORM basics, Alembic migrations.
- **Before Phase 3:** password hashing concepts, JWT structure/claims, FastAPI dependency injection.
- **Before Phases 4–6:** REST API design conventions, Pydantic schema validation, basic CRUD service/repository patterns.
- **Before Phase 7/9/10:** the actual academic math (weighted averages, solving for a variable in a percentage equation) — worth deriving by hand before coding, since these are the highest-stakes calculations in the app.
- **Before Phase 11:** basic scheduled-job concepts (cron or APScheduler).
- **Before Phase 14–16:** React data-fetching patterns (loading/error states), chart libraries if used (e.g., Chart.js/Recharts for basic visualizations).
- **Before Phase 17:** LLM prompt design, function/tool-calling if used, the concept of grounding/context injection.
- **Before Phase 18:** embeddings and vector similarity search basics, chunking strategies, pgvector or a vector DB of choice.
- **Before Phase 19:** OWASP API security basics, rate limiting concepts.
- **Before Phase 21–22:** Docker fundamentals (images/containers/compose), CI concepts (GitHub Actions YAML).
- **Before Phase 24:** core AWS services relevant here (ECS/Fargate, RDS, S3, CloudFront, IAM basics).

---

## 35. Recommended Project Folder Structure (Root Level)

```text
smart-university-cms/
├── backend/
│   ├── app/            (Section 10)
│   ├── tests/
│   ├── alembic/
│   ├── requirements.txt
│   └── .env.example
├── frontend/
│   ├── src/             (Section 9)
│   ├── public/
│   ├── package.json
│   └── .env.example
├── docs/
│   ├── phase0-architecture.md   (this document)
│   ├── decisions/                (one file per major decision, Section 36)
│   └── erd.png                    (once diagrammed visually)
├── docker-compose.yml   (Phase 21)
├── .github/workflows/   (Phase 22)
├── .gitignore
└── README.md
```

---

## 36. Major Architectural Decisions

**Decision: Modular monolith, not microservices.**
Why: solo developer, unproven load, and premature service boundaries create operational overhead (multiple deployments, network calls, distributed debugging) with no current benefit.
Alternative: microservices per module (auth, attendance, GPA, AI).
Why not chosen: adds deployment/ops complexity far beyond current team size (one person) and current scale (one institution).
Future expansion: module boundaries in `app/` (Section 8/10) are drawn so any module could be extracted into its own FastAPI service later if load or team size justifies it.

**Decision: Single-tenant schema now, tenant-aware design discipline from the start.**
Why: multi-tenancy adds complexity (row-level isolation, tenant-scoped queries everywhere) that isn't needed for a first deployment to one institution, but the entity model already treats `university_id` as a natural root (Section 11), so adding an `organization_id`/tenant column later is a migration, not a redesign.
Alternative: build full multi-tenant SaaS architecture now.
Why not chosen: over-engineering relative to Section 3's explicit guidance; real multi-tenant requirements (billing, tenant admin UX, cross-tenant security testing) aren't yet known.
Future expansion: if a second university signs on, introduce a `organizations` table above `universities` (or repurpose `universities` as the tenant root directly, since the hierarchy already starts there) and add tenant-scoping middleware/query filters.

**Decision: GPA/CGPA/attendance logic is deterministic backend code, never LLM-generated.**
Why: academic records have real consequences; LLMs are not reliable arithmetic engines and cannot be the audit-trail source of truth.
Alternative: let the AI compute and explain in one step.
Why not chosen: violates the explicit safety/accuracy requirement in your brief and would make the system untrustworthy for real deployment.
Future expansion: none needed — this boundary should hold permanently, even as AI capabilities grow.

**Decision: pgvector inside PostgreSQL (candidate) over a separate vector database, for RAG.**
Why: avoids introducing new infrastructure for what will likely be a modest policy-document corpus; keeps operational surface area small.
Alternative: dedicated vector DB (e.g., Pinecone, Weaviate, Qdrant).
Why not chosen for now: adds a new service to operate and pay for, unjustified at expected document volume.
Future expansion: revisit if document corpus or query volume grows enough that pgvector's performance becomes a bottleneck — this is a swappable implementation detail behind the RAG module's interface (Section 19), not a structural commitment.

**Decision: Railway + Vercel for initial deployment over AWS.**
Why: minimal ops overhead, fast iteration, git-push deploys, low cost for early-stage/portfolio use.
Alternative: AWS from day one.
Why not chosen: significantly higher setup/ops complexity for no current benefit; Section 3 explicitly discourages introducing complexity without a driving need.
Future expansion: Section 29 architecture is the defined migration target once real institutional scale, compliance, or cost requirements justify it.

**Decision: No `develop` branch; `main` + short-lived feature branches.**
Why: solo developer; a permanent second long-lived branch adds merge overhead without a team needing release isolation.
Alternative: full GitFlow (`main`/`develop`/`release`/`hotfix`).
Why not chosen: process overhead disproportionate to team size of one.
Future expansion: if collaborators join, a `develop` branch or trunk-based feature-flagging strategy can be introduced without restructuring history.

---

## Phase 0 Completion Checklist

- [x] Project vision, goals, and target users defined
- [x] Complete RBAC model across 6 roles, with explicit access boundaries
- [x] Full feature list captured and split into MVP vs Advanced
- [x] System architecture (current) and AI/RAG architecture (future) diagrammed
- [x] Frontend architecture and folder structure defined, with Redux explicitly deferred
- [x] Backend architecture and folder structure defined, with clear layer responsibilities
- [x] Conceptual database model covering all core entities, keys, and relationships
- [x] Conceptual ERD with relationship types identified
- [x] API structure, versioning, and conventions defined
- [x] Auth and RBAC enforcement strategy defined (route-level + service-level)
- [x] Deterministic business logic formulas specified for attendance/GPA/CGPA/recovery/target-feasibility
- [x] Notification generation strategy (immediate + scheduled) defined
- [x] AI architecture with explicit verified-data/AI-output separation
- [x] RAG architecture with ingestion, retrieval, and hallucination-prevention approach
- [x] Security architecture with phased rollout of measures
- [x] Audit logging scope defined
- [x] Configurable-vs-hardcoded academic rules distinction made
- [x] Git workflow, environment strategy, and testing strategy defined
- [x] Docker/CI-CD/deployment/AWS architecture defined as phased, not immediate
- [x] Scalability and data privacy considerations documented
- [x] Full 24-phase roadmap, phase dependencies, and pre-phase learning list documented
- [x] Major architectural decisions logged with alternatives and rationale

---

## Phase 1 Prerequisites

Before starting Phase 1 ("Project Setup"), have ready:

1. **Local environment:** Python (3.11+ recommended) and Node.js (LTS) installed; PostgreSQL installed locally or accessible via a local Docker container.
2. **Accounts (can be deferred until deployment, not needed to start coding):** GitHub repo created; Vercel and Railway accounts (only needed once you reach Phase 23).
3. **Decision confirmation:** confirm you're comfortable with the folder structures in Sections 9/10/35 — Phase 1 will scaffold exactly these.
4. **Naming decisions:** confirm the project's package/app name conventions (e.g., Python package name, npm project name) so scaffolding doesn't need renaming later.
5. **A `.env.example` mental checklist:** you should know roughly which environment variables you'll need (`DATABASE_URL`, `JWT_SECRET`, `CORS_ORIGINS`, later `LLM_API_KEY`) so Phase 1 sets up the config pattern correctly from the start.
6. **Mindset:** Phase 1 is scaffolding only — no business logic yet — so the goal is a clean, runnable "hello world" on both frontend and backend, connected to a real (empty) PostgreSQL database, with the folder structure from this document in place.

---

**End of Phase 0. Waiting for your explicit instruction: "Start Phase 1."**
