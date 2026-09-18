from __future__ import annotations

from datetime import datetime, timezone
from uuid import UUID

from fastapi import HTTPException
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models import (
    AcademicSession,
    Course,
    CourseOffering,
    Department,
    Enrollment,
    Program,
    Section,
    Semester,
    Student,
    Teacher,
)
from app.models.user import User, UserRole

MANAGE_ROLES = {
    UserRole.UNIVERSITY_ADMIN,
}


def ensure_org_user(user: User) -> UUID:
    if user.organization_id is None:
        raise HTTPException(
            status_code=403,
            detail="Organization membership required",
        )

    return user.organization_id


def require_manage(user: User) -> UUID:
    if user.role not in MANAGE_ROLES:
        raise HTTPException(
            status_code=403,
            detail="Organization administration permission required",
        )

    return ensure_org_user(user)


def commit(db: Session):
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(
            status_code=409,
            detail="Operation violates a database constraint",
        ) from exc


def list_scoped(
    db: Session,
    model,
    organization_id: UUID,
):
    return list(
        db.scalars(
            select(model)
            .where(
                model.organization_id == organization_id
            )
            .order_by(
                model.created_at.desc()
            )
        ).all()
    )


def get_scoped(
    db: Session,
    model,
    item_id: UUID,
    organization_id: UUID,
):
    return db.scalar(
        select(model).where(
            model.id == item_id,
            model.organization_id == organization_id,
        )
    )


# ============================================================
# COURSES
# ============================================================

def create_course(
    db: Session,
    payload,
    organization_id: UUID,
):
    department = get_scoped(
        db,
        Department,
        payload.department_id,
        organization_id,
    )

    if department is None:
        raise HTTPException(
            status_code=404,
            detail="Department not found",
        )

    item = Course(
        organization_id=organization_id,
        **payload.model_dump(),
    )

    db.add(item)
    commit(db)
    db.refresh(item)

    return item


def update_course(
    db: Session,
    item_id: UUID,
    payload,
    organization_id: UUID,
):
    item = get_scoped(
        db,
        Course,
        item_id,
        organization_id,
    )

    if item is None:
        raise HTTPException(
            status_code=404,
            detail="Course not found",
        )

    data = payload.model_dump(
        exclude_unset=True
    )

    if "department_id" in data:
        department = get_scoped(
            db,
            Department,
            data["department_id"],
            organization_id,
        )

        if department is None:
            raise HTTPException(
                status_code=404,
                detail="Department not found",
            )

    for key, value in data.items():
        setattr(item, key, value)

    commit(db)
    db.refresh(item)

    return item


def delete_course(
    db: Session,
    item_id: UUID,
    organization_id: UUID,
):
    item = get_scoped(
        db,
        Course,
        item_id,
        organization_id,
    )

    if item is None:
        raise HTTPException(
            status_code=404,
            detail="Course not found",
        )

    item.is_active = False

    commit(db)


# ============================================================
# COURSE OFFERINGS
# ============================================================

def validate_offering_relations(
    db: Session,
    course_id: UUID,
    section_id: UUID,
    academic_session_id: UUID,
    semester_id: UUID,
    teacher_id: UUID | None,
    organization_id: UUID,
):
    course = get_scoped(
        db,
        Course,
        course_id,
        organization_id,
    )

    if course is None:
        raise HTTPException(
            status_code=404,
            detail="Course not found",
        )

    section = get_scoped(
        db,
        Section,
        section_id,
        organization_id,
    )

    if section is None:
        raise HTTPException(
            status_code=404,
            detail="Section not found",
        )

    academic_session = get_scoped(
        db,
        AcademicSession,
        academic_session_id,
        organization_id,
    )

    if academic_session is None:
        raise HTTPException(
            status_code=404,
            detail="Academic session not found",
        )

    semester = get_scoped(
        db,
        Semester,
        semester_id,
        organization_id,
    )

    if semester is None:
        raise HTTPException(
            status_code=404,
            detail="Semester not found",
        )

    if teacher_id is not None:
        teacher = get_scoped(
            db,
            Teacher,
            teacher_id,
            organization_id,
        )

        if teacher is None:
            raise HTTPException(
                status_code=404,
                detail="Teacher not found",
            )

    return (
        course,
        section,
        academic_session,
        semester,
    )


def create_offering(
    db: Session,
    payload,
    organization_id: UUID,
):
    validate_offering_relations(
        db,
        payload.course_id,
        payload.section_id,
        payload.academic_session_id,
        payload.semester_id,
        payload.teacher_id,
        organization_id,
    )

    item = CourseOffering(
        organization_id=organization_id,
        **payload.model_dump(),
    )

    db.add(item)
    commit(db)
    db.refresh(item)

    return item


def list_offerings(
    db: Session,
    organization_id: UUID,
):
    return list_scoped(
        db,
        CourseOffering,
        organization_id,
    )


def get_offering(
    db: Session,
    item_id: UUID,
    organization_id: UUID,
):
    return get_scoped(
        db,
        CourseOffering,
        item_id,
        organization_id,
    )


def update_offering(
    db: Session,
    item_id: UUID,
    payload,
    organization_id: UUID,
):
    item = get_scoped(
        db,
        CourseOffering,
        item_id,
        organization_id,
    )

    if item is None:
        raise HTTPException(
            status_code=404,
            detail="Course offering not found",
        )

    data = payload.model_dump(
        exclude_unset=True
    )

    course_id = data.get(
        "course_id",
        item.course_id,
    )

    section_id = data.get(
        "section_id",
        item.section_id,
    )

    academic_session_id = data.get(
        "academic_session_id",
        item.academic_session_id,
    )

    semester_id = data.get(
        "semester_id",
        item.semester_id,
    )

    teacher_id = data.get(
        "teacher_id",
        item.teacher_id,
    )

    validate_offering_relations(
        db,
        course_id,
        section_id,
        academic_session_id,
        semester_id,
        teacher_id,
        organization_id,
    )

    for key, value in data.items():
        setattr(item, key, value)

    commit(db)
    db.refresh(item)

    return item


# ============================================================
# STUDENTS
# ============================================================

def list_students(
    db: Session,
    organization_id: UUID,
):
    return list_scoped(
        db,
        Student,
        organization_id,
    )


# ============================================================
# TEACHERS
# ============================================================

def list_teachers(
    db: Session,
    organization_id: UUID,
):
    return list_scoped(
        db,
        Teacher,
        organization_id,
    )


# ============================================================
# ENROLLMENTS
# ============================================================

def list_enrollments(
    db: Session,
    organization_id: UUID,
):
    return list_scoped(
        db,
        Enrollment,
        organization_id,
    )


def get_enrollment(
    db: Session,
    item_id: UUID,
    organization_id: UUID,
):
    return get_scoped(
        db,
        Enrollment,
        item_id,
        organization_id,
    )


def create_enrollment(
    db: Session,
    payload,
    organization_id: UUID,
    current_user: User,
):
    student_id = payload.student_id

    # If student_id is not supplied, try to use
    # the Student record connected to the logged-in user.
    if student_id is None:
        student = db.scalar(
            select(Student).where(
                Student.organization_id == organization_id,
                Student.user_id == current_user.id,
            )
        )

        if student is None:
            raise HTTPException(
                status_code=400,
                detail="Student ID is required for this user",
            )

        student_id = student.id

    else:
        student = get_scoped(
            db,
            Student,
            student_id,
            organization_id,
        )

        if student is None:
            raise HTTPException(
                status_code=404,
                detail="Student not found",
            )

    offering = get_scoped(
        db,
        CourseOffering,
        payload.course_offering_id,
        organization_id,
    )

    if offering is None:
        raise HTTPException(
            status_code=404,
            detail="Course offering not found",
        )

    if not offering.is_active:
        raise HTTPException(
            status_code=400,
            detail="Course offering is inactive",
        )

    # Check maximum enrollment capacity.
    if offering.max_students is not None:
        current_count = db.scalar(
            select(func.count(Enrollment.id)).where(
                Enrollment.organization_id == organization_id,
                Enrollment.course_offering_id == offering.id,
                Enrollment.status == "enrolled",
            )
        )

        if current_count >= offering.max_students:
            raise HTTPException(
                status_code=409,
                detail="Course offering has reached its maximum capacity",
            )

    # Prevent duplicate enrollment.
    existing = db.scalar(
        select(Enrollment).where(
            Enrollment.organization_id == organization_id,
            Enrollment.student_id == student_id,
            Enrollment.course_offering_id == offering.id,
        )
    )

    if existing is not None:
        raise HTTPException(
            status_code=409,
            detail="Student is already enrolled in this course offering",
        )

    item = Enrollment(
        organization_id=organization_id,
        student_id=student_id,
        course_offering_id=payload.course_offering_id,
    )

    db.add(item)
    commit(db)
    db.refresh(item)

    return item


def update_enrollment_status(
    db: Session,
    item_id: UUID,
    payload,
    organization_id: UUID,
):
    item = get_scoped(
        db,
        Enrollment,
        item_id,
        organization_id,
    )

    if item is None:
        raise HTTPException(
            status_code=404,
            detail="Enrollment not found",
        )

    item.status = payload.status

    if payload.status.value == "dropped":
        item.dropped_at = datetime.now(timezone.utc)
    else:
        item.dropped_at = None

    commit(db)
    db.refresh(item)

    return item