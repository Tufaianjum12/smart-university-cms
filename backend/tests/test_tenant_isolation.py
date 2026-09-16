"""Tenant isolation integration tests.

These tests intentionally use PostgreSQL. Set TEST_DATABASE_URL to an isolated test
PostgreSQL database before running them. They are not run against the development DB.
"""
import os
import uuid
import pytest
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session
from app.db.base import Base
from app.db.tenant import clear_current_organization, set_current_organization, TenantContextError
from app.models import Organization, OrganizationStatus, OrganizationType, Department, Campus, Course, Program, AcademicSession, Semester, Student, Section, Enrollment

TEST_DATABASE_URL = os.getenv("TEST_DATABASE_URL")
pytestmark = pytest.mark.skipif(not TEST_DATABASE_URL, reason="TEST_DATABASE_URL is not configured")


@pytest.fixture(scope="module")
def db_engine():
    engine = create_engine(TEST_DATABASE_URL, pool_pre_ping=True)
    Base.metadata.create_all(engine)
    yield engine
    Base.metadata.drop_all(engine)
    engine.dispose()


@pytest.fixture
def db(db_engine):
    with Session(db_engine) as session:
        yield session
        session.rollback()
    clear_current_organization()


def make_tenant(db, name, slug):
    org = Organization(name=name, slug=slug, organization_type=OrganizationType.UNIVERSITY, status=OrganizationStatus.ACTIVE)
    db.add(org); db.flush()
    return org


def make_course(db, org, suffix):
    campus = Campus(organization_id=org.id, name=f"Campus {suffix}", code=f"C-{suffix}")
    db.add(campus); db.flush()
    dept = Department(organization_id=org.id, campus_id=campus.id, name=f"Dept {suffix}", code=f"D-{suffix}")
    db.add(dept); db.flush()
    return Course(organization_id=org.id, department_id=dept.id, course_code=f"CS-{suffix}", title=f"Course {suffix}", credit_hours=3)


def test_same_tenant_query_returns_only_current_tenant(db):
    a = make_tenant(db, "Tenant A", "test-a")
    b = make_tenant(db, "Tenant B", "test-b")
    db.add(make_course(db, a, "A")); db.add(make_course(db, b, "B")); db.commit()
    set_current_organization(a.id)
    rows = db.scalars(select(Course).where(Course.organization_id == a.id)).all()
    assert len(rows) == 1 and rows[0].course_code == "CS-A"


def test_tenant_context_is_required():
    clear_current_organization()
    with pytest.raises(TenantContextError):
        from app.db.tenant import get_current_organization_id
        get_current_organization_id()


def test_cross_tenant_relationship_is_rejected_by_composite_fk(db):
    a = make_tenant(db, "Tenant A", "test-c")
    b = make_tenant(db, "Tenant B", "test-d")
    course_b = make_course(db, b, "B2"); db.add(course_b); db.flush()
    campus_a = Campus(organization_id=a.id, name="Campus A", code="CA")
    db.add(campus_a); db.flush()
    dept_a = Department(organization_id=a.id, campus_id=campus_a.id, name="Dept A", code="DA")
    db.add(dept_a); db.flush()
    prog_a = Program(organization_id=a.id, department_id=dept_a.id, name="Program A", code="PA")
    sess_a = AcademicSession(organization_id=a.id, code="2026", name="2026")
    db.add_all([prog_a, sess_a]); db.flush()
    sem_a = Semester(organization_id=a.id, academic_session_id=sess_a.id, code="FALL", name="Fall")
    db.add(sem_a); db.flush()
    section = Section(organization_id=a.id, course_id=course_b.id, semester_id=sem_a.id, program_id=prog_a.id, section_code="A")
    db.add(section)
    with pytest.raises(Exception):
        db.commit()
    db.rollback()
