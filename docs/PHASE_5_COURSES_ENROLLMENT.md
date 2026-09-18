# Phase 5 — Course Management & Enrollment

Phase 5 extends the Phase 4 multi-tenant CMS with course catalogue, prerequisites, program curriculum, semester-specific course offerings, teacher assignment, and enrollment.

## Design
- `Course` is reusable catalogue data.
- `CourseOffering` represents a course delivered to a specific section in an academic session/semester.
- `ProgramCourse` is the program curriculum association.
- `CoursePrerequisite` is a tenant-scoped self-referencing association.
- `Enrollment` connects a tenant-scoped `Student` to a `CourseOffering`.
- Composite foreign keys preserve tenant consistency at database level.
- Student self-enrollment derives the student from the authenticated user; a client cannot choose another tenant or student.
- Admin enrollment requires an explicit student ID but the student and offering are resolved inside the authenticated tenant.
- Section/program matching is enforced for enrollment. Cross-section enrollment is not allowed when the student's program/session does not match the offering section/context.
- Department Admin remains a foundation role because the current User model has no department assignment. Course administration is implemented for University Admin; Department Admin is included where the existing authorization architecture permits it, but future department scoping should be tied to a real user-department relationship.

## Phase boundary
Attendance, grades, GPA/CGPA, timetable, AI, deployment, billing, Docker and AWS are not implemented.
