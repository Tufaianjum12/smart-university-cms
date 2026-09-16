"""Run against a migrated PostgreSQL database to verify Phase 2 objects."""
from sqlalchemy import inspect
from app.db.session import engine

EXPECTED = {
    "organizations", "organization_settings", "users", "campuses", "departments", "programs",
    "academic_sessions", "semesters", "classrooms", "students", "teachers", "guardians",
    "student_guardians", "courses", "course_prerequisites", "sections", "enrollments",
    "attendance_records", "assessments", "grades", "timetable_entries", "notifications", "academic_targets",
}

with engine.connect() as conn:
    inspector = inspect(conn)
    tables = set(inspector.get_table_names())
    missing = EXPECTED - tables
    extra = tables - EXPECTED - {"alembic_version"}
    if missing:
        raise SystemExit(f"Missing tables: {sorted(missing)}")
    print(f"OK: {len(EXPECTED)} Phase 2 tables exist.")
    if extra:
        print(f"Note: additional tables found: {sorted(extra)}")
    for table in sorted(EXPECTED):
        fk_count = len(inspector.get_foreign_keys(table))
        print(f"{table}: {fk_count} foreign keys")
