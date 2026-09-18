from __future__ import annotations

from datetime import datetime, timezone
from uuid import UUID

from fastapi import HTTPException
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.db.tenant import get_current_organization_id

from app.models import (
    Course,
    CoursePrerequisite,
    ProgramCourse,
    CourseOffering,
    Enrollment,
    Department,
    Program,
    Semester,
    AcademicSession,
    Section,
    Teacher,
    Student,
    EnrollmentStatus,
)

from app.models.academic import CourseType


MANAGE_ROLES = {"university_admin"}


# ============================================================
# TENANT
# ============================================================

def oid() -> UUID:
    value = get_current_organization_id()

    if value is None:
        raise HTTPException(
            status_code=403,
            detail="Organization membership required",
        )

    return value


# ============================================================
# GENERAL HELPERS
# ============================================================

def fail(name: str):
    raise HTTPException(
        status_code=404,
        detail=f"{name} not found",
    )


def scoped(
    db: Session,
    model,
    ident: UUID,
):
    return db.scalar(
        select(model).where(
            model.organization_id == oid(),
            model.id == ident,
        )
    )


def list_scoped(
    db: Session,
    model,
):
    """
    Return tenant-scoped records.

    Courses use soft deletion, so archived courses are excluded
    from the normal course listing.

    Other models keep the existing behavior.
    """

    statement = select(model).where(
        model.organization_id == oid()
    )

    # Courses are soft-deleted.
    # Archived courses should not appear in the normal list.
    if model is Course:
        statement = statement.where(
            Course.is_active.is_(True)
        )

    statement = statement.order_by(
        model.created_at.desc()
    )

    return list(
        db.scalars(statement).all()
    )


def get_or_404(
    db: Session,
    model,
    ident: UUID,
    name: str,
):
    obj = scoped(
        db,
        model,
        ident,
    )

    if obj is None:
        fail(name)

    return obj


def commit(db: Session):
    try:
        db.commit()

    except IntegrityError as e:
        db.rollback()

        raise HTTPException(
            status_code=409,
            detail="Operation violates a database constraint",
        ) from e


# ============================================================
# COURSES
# ============================================================

def create_course(
    db: Session,
    p,
):
    data = p.model_dump()

    get_or_404(
        db,
        Department,
        data["department_id"],
        "Department",
    )

    course = Course(
        organization_id=oid(),
        **data,
    )

    db.add(course)

    commit(db)

    db.refresh(course)

    return course


def update_course(
    db: Session,
    course_id: UUID,
    p,
):
    course = get_or_404(
        db,
        Course,
        course_id,
        "Course",
    )

    data = p.model_dump(
        exclude_unset=True
    )

    if "department_id" in data:
        get_or_404(
            db,
            Department,
            data["department_id"],
            "Department",
        )

    for key, value in data.items():
        setattr(
            course,
            key,
            value,
        )

    commit(db)

    db.refresh(course)

    return course


def archive_course(
    db: Session,
    course_id: UUID,
):
    course = get_or_404(
        db,
        Course,
        course_id,
        "Course",
    )

    course.is_active = False

    commit(db)


# ============================================================
# COURSE PREREQUISITES
# ============================================================

def add_prereq(
    db: Session,
    course_id: UUID,
    p,
):
    course = get_or_404(
        db,
        Course,
        course_id,
        "Course",
    )

    prerequisite_course = get_or_404(
        db,
        Course,
        p.prerequisite_course_id,
        "Prerequisite course",
    )

    if course.id == prerequisite_course.id:
        raise HTTPException(
            status_code=400,
            detail="A course cannot be its own prerequisite",
        )

    prerequisite = CoursePrerequisite(
        organization_id=oid(),
        course_id=course.id,
        prerequisite_course_id=prerequisite_course.id,
    )

    db.add(prerequisite)

    commit(db)

    db.refresh(prerequisite)

    return prerequisite


def list_prereq(
    db: Session,
    course_id: UUID,
):
    get_or_404(
        db,
        Course,
        course_id,
        "Course",
    )

    return list(
        db.scalars(
            select(CoursePrerequisite)
            .where(
                CoursePrerequisite.organization_id == oid(),
                CoursePrerequisite.course_id == course_id,
            )
        ).all()
    )


def remove_prereq(
    db: Session,
    prerequisite_id: UUID,
):
    prerequisite = get_or_404(
        db,
        CoursePrerequisite,
        prerequisite_id,
        "Prerequisite",
    )

    db.delete(prerequisite)

    commit(db)


# ============================================================
# PROGRAM CURRICULUM
# ============================================================

def add_curriculum(
    db: Session,
    program_id: UUID,
    p,
):
    program = get_or_404(
        db,
        Program,
        program_id,
        "Program",
    )

    course = get_or_404(
        db,
        Course,
        p.course_id,
        "Course",
    )

    if p.recommended_semester_id:
        get_or_404(
            db,
            Semester,
            p.recommended_semester_id,
            "Semester",
        )

    curriculum = ProgramCourse(
        organization_id=oid(),
        program_id=program.id,
        **p.model_dump(),
    )

    db.add(curriculum)

    commit(db)

    db.refresh(curriculum)

    return curriculum


def list_curriculum(
    db: Session,
    program_id: UUID,
):
    get_or_404(
        db,
        Program,
        program_id,
        "Program",
    )

    return list(
        db.scalars(
            select(ProgramCourse)
            .where(
                ProgramCourse.organization_id == oid(),
                ProgramCourse.program_id == program_id,
            )
            .order_by(
                ProgramCourse.sort_order,
                ProgramCourse.created_at,
            )
        ).all()
    )


def update_curriculum(
    db: Session,
    curriculum_id: UUID,
    p,
):
    curriculum = get_or_404(
        db,
        ProgramCourse,
        curriculum_id,
        "Curriculum entry",
    )

    data = p.model_dump(
        exclude_unset=True
    )

    if (
        "recommended_semester_id" in data
        and data["recommended_semester_id"]
    ):
        get_or_404(
            db,
            Semester,
            data["recommended_semester_id"],
            "Semester",
        )

    if "course_id" in data:
        get_or_404(
            db,
            Course,
            data["course_id"],
            "Course",
        )

    if "program_id" in data:
        get_or_404(
            db,
            Program,
            data["program_id"],
            "Program",
        )

    for key, value in data.items():
        setattr(
            curriculum,
            key,
            value,
        )

    commit(db)

    db.refresh(curriculum)

    return curriculum


def remove_curriculum(
    db: Session,
    curriculum_id: UUID,
):
    curriculum = get_or_404(
        db,
        ProgramCourse,
        curriculum_id,
        "Curriculum entry",
    )

    db.delete(curriculum)

    commit(db)


# ============================================================
# COURSE OFFERINGS
# ============================================================

def validate_offering_relations(
    db: Session,
    data: dict,
):
    course = get_or_404(
        db,
        Course,
        data["course_id"],
        "Course",
    )

    section = get_or_404(
        db,
        Section,
        data["section_id"],
        "Section",
    )

    academic_session = get_or_404(
        db,
        AcademicSession,
        data["academic_session_id"],
        "Academic session",
    )

    semester = get_or_404(
        db,
        Semester,
        data["semester_id"],
        "Semester",
    )

    # Semester must belong to selected academic session.
    if semester.academic_session_id != academic_session.id:
        raise HTTPException(
            status_code=400,
            detail="Semester does not belong to the academic session",
        )

    # Section must belong to selected semester.
    if section.semester_id != semester.id:
        raise HTTPException(
            status_code=400,
            detail="Section does not belong to the selected semester",
        )

    # Legacy section/course compatibility.
    if (
        section.course_id is not None
        and section.course_id != course.id
    ):
        raise HTTPException(
            status_code=400,
            detail=(
                "Section is already associated "
                "with a different legacy course"
            ),
        )

    # Teacher validation.
    if data.get("teacher_id") is not None:
        get_or_404(
            db,
            Teacher,
            data["teacher_id"],
            "Teacher",
        )

    # All required academic entities must be active.
    if not course.is_active:
        raise HTTPException(
            status_code=400,
            detail="Course, section, session and semester must be active",
        )

    if not section.is_active:
        raise HTTPException(
            status_code=400,
            detail="Course, section, session and semester must be active",
        )

    if not academic_session.is_active:
        raise HTTPException(
            status_code=400,
            detail="Course, section, session and semester must be active",
        )

    if not semester.is_active:
        raise HTTPException(
            status_code=400,
            detail="Course, section, session and semester must be active",
        )

    return (
        course,
        section,
        academic_session,
        semester,
    )


def create_offering(
    db: Session,
    p,
):
    data = p.model_dump()

    validate_offering_relations(
        db,
        data,
    )

    offering = CourseOffering(
        organization_id=oid(),
        **data,
    )

    db.add(offering)

    commit(db)

    db.refresh(offering)

    return offering


def update_offering(
    db: Session,
    offering_id: UUID,
    p,
):
    offering = get_or_404(
        db,
        CourseOffering,
        offering_id,
        "Course offering",
    )

    data = p.model_dump(
        exclude_unset=True
    )

    merged = {
        key: getattr(offering, key)
        for key in [
            "course_id",
            "section_id",
            "academic_session_id",
            "semester_id",
            "teacher_id",
            "max_students",
        ]
    }

    merged.update(
        {
            key: value
            for key, value in data.items()
            if key != "is_active"
        }
    )

    validate_offering_relations(
        db,
        merged,
    )

    for key, value in data.items():
        setattr(
            offering,
            key,
            value,
        )

    commit(db)

    db.refresh(offering)

    return offering


def archive_offering(
    db: Session,
    offering_id: UUID,
):
    offering = get_or_404(
        db,
        CourseOffering,
        offering_id,
        "Course offering",
    )

    offering.is_active = False

    commit(db)


def list_offerings_for_user(
    db: Session,
    user,
):
    # Administrators and teachers can see all tenant offerings.
    if user.role.value != "student":
        return list_scoped(
            db,
            CourseOffering,
        )

    student = _student_for_user(
        db,
        user,
    )

    if student is None:
        return []

    return list(
        db.scalars(
            select(CourseOffering)
            .join(
                Section,
                (
                    Section.organization_id
                    == CourseOffering.organization_id
                )
                & (
                    Section.id
                    == CourseOffering.section_id
                ),
            )
            .where(
                CourseOffering.organization_id == oid(),
                CourseOffering.is_active.is_(True),
                Section.program_id == student.program_id,
                CourseOffering.academic_session_id
                == student.academic_session_id,
            )
            .order_by(
                CourseOffering.created_at.desc()
            )
        ).all()
    )


# ============================================================
# STUDENTS / TEACHERS
# ============================================================

def _student_for_user(
    db: Session,
    user,
):
    return db.scalar(
        select(Student).where(
            Student.organization_id == oid(),
            Student.user_id == user.id,
        )
    )


# ============================================================
# ENROLLMENTS
# ============================================================

def create_enrollment(
    db: Session,
    p,
    user,
    admin: bool = False,
):
    # --------------------------------------------------------
    # Determine student
    # --------------------------------------------------------

    if not admin:
        student = _student_for_user(
            db,
            user,
        )

        if student is None:
            raise HTTPException(
                status_code=403,
                detail="Student profile is required for enrollment",
            )

        student_id = student.id

        if (
            p.student_id is not None
            and p.student_id != student_id
        ):
            raise HTTPException(
                status_code=403,
                detail="Students may only enroll themselves",
            )

    else:
        if p.student_id is None:
            raise HTTPException(
                status_code=422,
                detail=(
                    "student_id is required "
                    "for administrator enrollment"
                ),
            )

        student_id = p.student_id

    student = get_or_404(
        db,
        Student,
        student_id,
        "Student",
    )

    # --------------------------------------------------------
    # Lock offering row while checking capacity
    # --------------------------------------------------------

    offering = db.scalar(
        select(CourseOffering)
        .where(
            CourseOffering.organization_id == oid(),
            CourseOffering.id == p.course_offering_id,
        )
        .with_for_update()
    )

    if offering is None:
        fail("Course offering")

    # --------------------------------------------------------
    # Validate student
    # --------------------------------------------------------

    if student.status.value != "active":
        raise HTTPException(
            status_code=400,
            detail="Inactive students cannot enroll",
        )

    if not offering.is_active:
        raise HTTPException(
            status_code=400,
            detail="Course offering is not active",
        )

    section = get_or_404(
        db,
        Section,
        offering.section_id,
        "Section",
    )

    # Student program must match section program.
    if student.program_id != section.program_id:
        raise HTTPException(
            status_code=400,
            detail=(
                "Student program does not match "
                "the course offering section"
            ),
        )

    # Student academic session must match offering.
    if (
        student.academic_session_id
        != offering.academic_session_id
    ):
        raise HTTPException(
            status_code=400,
            detail=(
                "Student academic session does not "
                "match the offering"
            ),
        )

    # --------------------------------------------------------
    # Duplicate enrollment check
    # --------------------------------------------------------

    existing = db.scalar(
        select(Enrollment).where(
            Enrollment.organization_id == oid(),
            Enrollment.student_id == student_id,
            Enrollment.course_offering_id
            == offering.id,
        )
    )

    if existing:
        raise HTTPException(
            status_code=409,
            detail=(
                "Student is already enrolled "
                "in this course offering"
            ),
        )

    # --------------------------------------------------------
    # Capacity check
    # --------------------------------------------------------

    if offering.max_students is not None:
        count = db.scalar(
            select(func.count())
            .select_from(Enrollment)
            .where(
                Enrollment.organization_id == oid(),
                Enrollment.course_offering_id
                == offering.id,
                Enrollment.status
                == EnrollmentStatus.ENROLLED,
            )
        ) or 0

        if count >= offering.max_students:
            raise HTTPException(
                status_code=409,
                detail="Course offering capacity has been reached",
            )

    # --------------------------------------------------------
    # Create enrollment
    # --------------------------------------------------------

    enrollment = Enrollment(
        organization_id=oid(),
        student_id=student_id,
        course_offering_id=offering.id,
    )

    db.add(enrollment)

    commit(db)

    db.refresh(enrollment)

    return enrollment


def list_enrollments(
    db: Session,
    student_id: UUID | None = None,
    offering_id: UUID | None = None,
):
    statement = select(Enrollment).where(
        Enrollment.organization_id == oid()
    )

    if student_id:
        statement = statement.where(
            Enrollment.student_id == student_id
        )

    if offering_id:
        statement = statement.where(
            Enrollment.course_offering_id
            == offering_id
        )

    statement = statement.order_by(
        Enrollment.created_at.desc()
    )

    return list(
        db.scalars(statement).all()
    )


def get_enrollment(
    db: Session,
    enrollment_id: UUID,
):
    return get_or_404(
        db,
        Enrollment,
        enrollment_id,
        "Enrollment",
    )


def update_enrollment(
    db: Session,
    enrollment_id: UUID,
    p,
):
    enrollment = get_enrollment(
        db,
        enrollment_id,
    )

    enrollment.status = p.status

    if p.status in {
        EnrollmentStatus.DROPPED,
        EnrollmentStatus.WITHDRAWN,
    }:
        enrollment.dropped_at = datetime.now(
            timezone.utc
        )
    else:
        enrollment.dropped_at = None

    commit(db)

    db.refresh(enrollment)

    return enrollment