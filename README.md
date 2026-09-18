# 🎓 Smart University Academic Management System

A professional **multi-tenant SaaS Academic Management System** designed for universities, colleges, and educational institutes.

The system is being developed with a modern full-stack architecture using **React, FastAPI, PostgreSQL, JWT authentication, and tenant-isolated data architecture**, with future integration of **AI, RAG, and intelligent academic assistance**.

---

## 🚀 Project Status

**Current Phase: Phase 5 — Course Management & API Testing**

The project is currently in the backend/API development and testing stage.

### Completed Foundation

* ✅ Multi-tenant SaaS architecture
* ✅ Organization/University management foundation
* ✅ Tenant-isolated database architecture
* ✅ JWT authentication
* ✅ Role-based security foundation
* ✅ Academic structure management
* ✅ Course management foundation
* ✅ Enrollment foundation
* ✅ FastAPI REST APIs
* ✅ Swagger/OpenAPI documentation
* ✅ PostgreSQL database
* ✅ Alembic database migrations
* ✅ Development seed data
* ✅ API testing with Swagger
* ✅ Postman API testing setup
* 🔄 Complete API regression and security testing in progress
* ⏳ React frontend development continues in later phases
* ⏳ AI/RAG integration planned for later phases

---

# 🏗️ Technology Stack

## Frontend

* React
* Vite
* JavaScript
* Bootstrap 5
* Bootstrap Icons
* React Router
* Axios

## Backend

* Python
* FastAPI
* SQLAlchemy
* Pydantic
* Alembic
* JWT Authentication
* Role-Based Access Control

## Database

* PostgreSQL

## API Development & Testing

* FastAPI Swagger/OpenAPI
* Postman
* REST APIs
* JSON
* JWT Bearer Authentication

## Future Technologies

* LLM
* RAG
* Embeddings
* Vector Database
* AI Academic Assistant
* Docker
* GitHub Actions
* AWS

---

# 🏢 Multi-Tenant SaaS Architecture

The system is designed as a **multi-tenant SaaS from the beginning**.

The main tenant is an educational organization such as:

* University
* College
* Institute
* Campus-based organization

Each organization has its own isolated academic data.

### Example

```text
Super Admin
     │
     ├── University A
     │      ├── Campus
     │      ├── Departments
     │      ├── Programs
     │      ├── Teachers
     │      ├── Students
     │      └── Courses
     │
     └── University B
            ├── Campus
            ├── Departments
            ├── Programs
            ├── Teachers
            ├── Students
            └── Courses
```

A user belonging to **University A must not be able to access University B's data**.

Tenant isolation is enforced at the backend/database access layer.

---

# 👥 Planned User Roles

The system is designed around the following roles:

| Role             | Responsibility                                      |
| ---------------- | --------------------------------------------------- |
| Super Admin      | Manage organizations and global SaaS administration |
| University Admin | Manage organization-level academic operations       |
| Department Admin | Manage department academic data                     |
| Teacher          | Manage teaching activities                          |
| Student          | Access courses, academic information and activities |
| Parent/Guardian  | Monitor student academic information                |

Additional permissions and role restrictions will continue to be implemented as the system grows.

---

# 🧩 Development Phases

## Phase 0 — Architecture & Planning

### Completed

The initial architecture and project structure were established.

Major decisions included:

* Multi-tenant SaaS architecture
* React + FastAPI architecture
* PostgreSQL database
* JWT authentication strategy
* Role-based access control
* Tenant isolation strategy
* Academic domain structure
* Future AI/RAG architecture
* Deployment architecture

---

# Phase 1 — Project Setup

### Completed

Initial development environment and project foundation were created.

### Backend

```text
backend/
└── app/
    ├── api/
    ├── core/
    ├── models/
    ├── schemas/
    ├── services/
    ├── repositories/
    └── main.py
```

Initial backend technologies:

* FastAPI
* SQLAlchemy
* PostgreSQL
* Pydantic
* Alembic

Development environment and database connectivity were established.

---

# Phase 2 — Database & Academic Foundation

The database architecture was developed around the academic domain.

Initial academic entities include:

* Organization
* Campus
* Department
* Program
* Academic Session
* Semester
* Classroom
* Section

The models were designed with tenant-aware relationships to support SaaS data isolation.

---

# Phase 3 — Multi-Tenant Foundation & Security

## 🔐 Authentication

JWT-based authentication was implemented.

The system supports:

```text
Login
  ↓
JWT Access Token
  ↓
Authenticated API Request
  ↓
User Identity
  ↓
Organization/Tenant Context
  ↓
Permission Validation
```

### Authentication API

```http
POST /api/v1/auth/login
```

```http
GET /api/v1/auth/me
```

---

## 🔒 Tenant Isolation

Tenant-aware models and repositories were implemented.

The architecture ensures that organization-specific records are associated with the correct tenant.

Example:

```text
University A
    ↓
tenant_id = A

University B
    ↓
tenant_id = B
```

API access is validated against the authenticated user's organization.

---

## 🧪 Security Testing

Security-related foundations and tests were added for:

* Authentication
* JWT validation
* Tenant context
* Authorization
* Super Admin access
* Cross-tenant protection

---

## 🌱 Development Seed Data

Development organizations were created for testing.

```text
dev-university-a
dev-college-b
```

Development accounts were also seeded for testing authentication and tenant isolation.

---

# Phase 4 — Organization & Academic Structure Management

Phase 4 focused on building the academic organization structure and related management APIs.

## 🏢 Organization Management

The system supports organization-level management including:

* Organization creation
* Organization information
* Organization activation/suspension foundation
* Organization settings foundation

---

## 🏫 Campus Management

Academic organizations can contain campuses.

```text
Organization
    ↓
Campus
```

---

## 🏛️ Department Management

Departments belong to an organization/campus structure.

Example:

```text
University
   ↓
Campus
   ↓
Department
```

---

## 🎓 Program Management

Programs can be associated with academic departments.

Examples:

```text
BS Software Engineering
BS Computer Science
BS Information Technology
```

---

## 📚 Academic Sessions

Academic sessions provide the time structure for academic operations.

Example:

```text
2026 - 2027
```

---

## 📅 Semesters

Academic sessions can contain semesters.

Example:

```text
Fall 2026
Spring 2027
```

---

## 🏫 Classrooms

Classroom management was included as part of the academic structure.

---

## 👨‍🎓 Sections

Sections provide academic grouping within programs/courses.

Example:

```text
BS Software Engineering
        ↓
5th Semester
        ↓
Section A
Section B
```

---

# Phase 5 — Course Management, Enrollment & API Testing

Phase 5 extends the academic system toward actual teaching and student enrollment.

## 📚 Course Management

The course management layer is designed to support:

* Course creation
* Course updates
* Course retrieval
* Course deletion
* Course codes
* Credit hours
* Course types
* Department association
* Program curriculum relationships
* Prerequisites

Example:

```text
Department
     ↓
Program
     ↓
Course
```

---

## 📖 Course Offerings

Courses can be associated with academic structures such as:

* Academic Session
* Semester
* Section
* Teacher assignment foundation

Example:

```text
Course
   ↓
Academic Session
   ↓
Semester
   ↓
Section
```

---

# 👨‍🎓 Student Enrollment

Enrollment functionality is being developed to connect students with course offerings.

Example:

```text
Student
   ↓
Enrollment
   ↓
Course Offering
   ↓
Course
```

Enrollment statuses can be used to represent the student's enrollment state.

---

# 🔌 REST API Architecture

The backend follows a versioned API structure.

```text
/api/v1/
```

Example:

```text
/api/v1/auth/login
/api/v1/auth/me
/api/v1/organizations
/api/v1/campuses
/api/v1/departments
/api/v1/programs
/api/v1/academic-sessions
/api/v1/semesters
/api/v1/classrooms
/api/v1/sections
/api/v1/courses
```

The exact available endpoints continue to expand as each module is completed.

---

# 📖 API Documentation

FastAPI automatically provides interactive API documentation.

### Swagger UI

```text
http://127.0.0.1:8000/docs
```

### OpenAPI JSON

```text
http://127.0.0.1:8000/openapi.json
```

Swagger is currently being used to manually verify API behavior.

---

# 🧪 API Testing

API testing has been started using:

## Swagger

Swagger is used for:

* Endpoint testing
* Request body validation
* JWT authorization
* Response verification
* HTTP status code verification

## Postman

The OpenAPI specification can be imported into Postman.

Example local environment:

```text
base_url = http://127.0.0.1:8000
access_token = <JWT token>
```

Authenticated requests use:

```text
Authorization: Bearer {{access_token}}
```

---

# 🔐 Authentication Testing Flow

The current API testing workflow is:

```text
1. Start FastAPI server
        ↓
2. Open Swagger/Postman
        ↓
3. Login
        ↓
4. Receive JWT access token
        ↓
5. Store access token
        ↓
6. Send authenticated requests
        ↓
7. Verify API response
        ↓
8. Test authorization and tenant isolation
```

---

# 🧪 Planned API Test Coverage

API testing is being expanded across the system.

Testing includes:

### Functional Testing

* GET
* POST
* PUT/PATCH
* DELETE

### Validation Testing

* Missing fields
* Invalid data
* Invalid IDs
* Invalid relationships
* Duplicate records

### Security Testing

* Missing authentication
* Invalid JWT
* Expired/invalid token
* Unauthorized access
* Role restrictions
* Cross-tenant access

### HTTP Responses

Examples:

```text
200 OK
201 Created
400 Bad Request
401 Unauthorized
403 Forbidden
404 Not Found
422 Unprocessable Entity
```

---

# 🗄️ Database Architecture

PostgreSQL is the primary database.

SQLAlchemy is used as the ORM.

Alembic is used for database migrations.

General relationship:

```text
Organization
    │
    ├── Campus
    │      └── Department
    │             └── Program
    │                    └── Course
    │
    ├── Academic Sessions
    │      └── Semesters
    │
    └── Users
           ├── Admin
           ├── Teacher
           └── Student
```

---

# 📁 Current Backend Architecture

The backend follows a layered architecture.

```text
backend/
│
├── app/
│   ├── api/
│   │   └── v1/
│   │
│   ├── core/
│   │
│   ├── models/
│   │
│   ├── schemas/
│   │
│   ├── repositories/
│   │
│   ├── services/
│   │
│   ├── security/
│   │
│   └── main.py
│
├── alembic/
│
├── tests/
│
├── requirements.txt
└── seed_dev.py
```

---

# ❤️ Health Check

The backend provides health-check endpoints.

```http
GET /health
```

```http
GET /api/v1/health
```

Example successful response:

```json
{
  "status": "ok"
}
```

The development environment has also been verified with PostgreSQL connectivity.

---

# 🤖 Future AI Architecture

AI functionality is **not the core of the current Phase 5 implementation**.

It is planned for later phases.

The planned AI architecture includes:

```text
University Documents
       ↓
Document Processing
       ↓
Embeddings
       ↓
Vector Database
       ↓
RAG Retrieval
       ↓
LLM
       ↓
AI Academic Assistant
```

Potential use cases:

* University policy questions
* Course information
* Academic guidance
* Document-based Q&A
* Student academic assistant
* University knowledge assistant

### Important Design Principle

Deterministic academic calculations will remain backend-controlled.

For example:

```text
GPA
CGPA
Attendance %
Required attendance
Target GPA
Recovery calculations
```

These calculations should be performed by deterministic backend logic rather than relying on an LLM.

---

# 🛣️ Future Development Roadmap

Planned future modules include:

### Phase 6+

* Student management
* Teacher management
* Enrollment expansion
* Attendance
* Assignments
* Exams
* Grades
* GPA/CGPA engine
* Timetable
* Notifications
* Parent/Guardian portal

### Later AI Phases

* AI Academic Assistant
* RAG
* Embeddings
* Vector Database
* University document Q&A
* AI-powered academic support

### Deployment

Planned deployment architecture:

```text
React/Vite
     ↓
Vercel

FastAPI
     ↓
Railway / AWS

PostgreSQL
     ↓
Managed PostgreSQL
```

Future infrastructure may include:

* Docker
* GitHub Actions
* AWS
* CI/CD
* Production monitoring

---

# 🔐 Security Goals

Security is a core requirement of the project.

The system is being designed to provide:

* JWT authentication
* Role-based authorization
* Tenant isolation
* Secure password handling
* API validation
* Database constraints
* Cross-tenant access prevention
* Protected administrative endpoints

---

# 🎯 Project Vision

The long-term goal is to transform the project into a **production-ready SaaS platform for educational organizations**.

The intended platform will allow an organization to manage:

```text
Organization
      ↓
Users
      ↓
Departments
      ↓
Programs
      ↓
Courses
      ↓
Enrollment
      ↓
Attendance
      ↓
Assignments
      ↓
Exams
      ↓
Grades
      ↓
GPA / CGPA
      ↓
Timetable
      ↓
AI Academic Assistant
```

The architecture is being developed with scalability, security, tenant isolation, and future commercialization in mind.

---

# 📊 Current Progress

| Area                        | Status         |
| --------------------------- | -------------- |
| Project Architecture        | ✅ Completed    |
| Multi-Tenant Foundation     | ✅ Completed    |
| PostgreSQL                  | ✅ Implemented  |
| SQLAlchemy                  | ✅ Implemented  |
| Alembic                     | ✅ Implemented  |
| JWT Authentication          | ✅ Implemented  |
| Security Foundation         | ✅ Implemented  |
| Organization Management     | ✅ Implemented  |
| Campus Management           | ✅ Implemented  |
| Department Management       | ✅ Implemented  |
| Program Management          | ✅ Implemented  |
| Academic Sessions           | ✅ Implemented  |
| Semesters                   | ✅ Implemented  |
| Classrooms                  | ✅ Implemented  |
| Sections                    | ✅ Implemented  |
| Course Management           | 🔄 Phase 5     |
| Enrollment                  | 🔄 Phase 5     |
| Swagger Testing             | ✅ In Progress  |
| Postman Testing             | 🔄 In Progress |
| Full API Regression Testing | 🔄 In Progress |
| Student Portal              | ⏳ Planned      |
| Teacher Portal              | ⏳ Planned      |
| Attendance                  | ⏳ Planned      |
| Assignments                 | ⏳ Planned      |
| Exams                       | ⏳ Planned      |
| GPA/CGPA Engine             | ⏳ Planned      |
| Timetable                   | ⏳ Planned      |
| AI Assistant                | ⏳ Planned      |
| RAG                         | ⏳ Planned      |
| Production Deployment       | ⏳ Planned      |

---

# 🧑‍💻 Developer

**Tufail Anjum**

BS Software Engineering
University of Engineering & Technology (UET) Mardan

### GitHub

```text
https://github.com/Tufaianjum12
```

---

# 📜 License

This project is currently under active development.

License and production/commercial usage terms will be defined before public production release.
