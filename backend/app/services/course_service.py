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
    CoursePrerequisite,
    Department,
    Enrollment,
    EnrollmentStatus,
    Program,
    ProgramCourse,
    Section,
    Semester,
    Student,
    Teacher,
)
from app.models.academic import CourseType
MANAGE_ROLES = {"university_admin"}
# ============================================================
# TENANT
# ============================================================
def oid(db: Session):
    """
    Get the current organization/tenant ID from the SQLAlchemy
    session.
    The organization_id is stored in db.info by get_current_user().
    This is safer than relying only on ContextVar because synchronous
    FastAPI endpoints may execute in a worker thread.
    """
    value = db.info.get("organization_id")
    if value is None:
        raise HTTPException(
            status_code=403,
            detail="Organization membership required",
        )
    return value
# ============================================================
# COMMON HELPERS
# ============================================================
def fail(name: str):
    raise HTTPException(
        status_code=404,
        detail=f"{name} not found",
    )
def scoped(db: Session, model, ident):
    return db.scalar(
        select(model).where(
            model.organization_id == oid(db),
            model.id == ident,
        )
    )
def list_scoped(db: Session, model):
    return list(
        db.scalars(
            select(model)
            .where(model.organization_id == oid(db))
            .order_by(model.created_at.desc())
        ).all()
    )
def get_or_404(db: Session, model, ident, name: str):
    obj = scoped(db, model, ident)
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
def create_course(db: Session, p):
    d = p.model_dump()
    get_or_404(
        db,
        Department,
        d["department_id"],
        "Department",
    )
    x = Course(
        organization_id=oid(db),
        **d,
    )
    db.add(x)
    commit(db)
    db.refresh(x)
    return x
def update_course(db: Session, i: UUID, p):
    x = get_or_404(
        db,
        Course,
        i,
        "Course",
    )
    d = p.model_dump(exclude_unset=True)
    if "department_id" in d:
        get_or_404(
            db,
            Department,
            d["department_id"],
            "Department",
        )
    for k, v in d.items():
        setattr(x, k, v)
    commit(db)
    db.refresh(x)
    return x
def archive_course(db: Session, i: UUID):
    x = get_or_404(
        db,
        Course,
        i,
        "Course",
    )
    x.is_active = False
    commit(db)
# ============================================================
# COURSE PREREQUISITES
# ============================================================
def add_prereq(db: Session, course_id: UUID, p):
    course = get_or_404(
        db,
        Course,
        course_id,
        "Course",
    )
    pre = get_or_404(
        db,
        Course,
        p.prerequisite_course_id,
        "Prerequisite course",
    )
    if course.id == pre.id:
        raise HTTPException(
            status_code=400,
            detail="A course cannot be its own prerequisite",
        )
    x = CoursePrerequisite(
        organization_id=oid(db),
        course_id=course.id,
        prerequisite_course_id=pre.id,
    )
    db.add(x)
    commit(db)
    db.refresh(x)
    return x
def list_prereq(db: Session, course_id: UUID):
    get_or_404(
        db,
        Course,
        course_id,
        "Course",
    )
    return list(
        db.scalars(
            select(CoursePrerequisite).where(
                CoursePrerequisite.organization_id == oid(db),
                CoursePrerequisite.course_id == course_id,
            )
        ).all()
    )
def remove_prereq(db: Session, i: UUID):
    x = get_or_404(
        db,
        CoursePrerequisite,
        i,
        "Prerequisite",
    )
    db.delete(x)
    commit(db)
# ============================================================
# PROGRAM CURRICULUM
# ============================================================
def add_curriculum(db: Session, program_id: UUID, p):
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
    x = ProgramCourse(
        organization_id=oid(db),
        program_id=program.id,
        **p.model_dump(),
    )
    db.add(x)
    commit(db)
    db.refresh(x)
    return x
def list_curriculum(db: Session, program_id: UUID):
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
                ProgramCourse.organization_id == oid(db),
                ProgramCourse.program_id == program_id,
            )
            .order_by(
                ProgramCourse.sort_order,
                ProgramCourse.created_at,
            )
        ).all()
    )
def update_curriculum(db: Session, i: UUID, p):
    x = get_or_404(
        db,
        ProgramCourse,
        i,
        "Curriculum entry",
    )
    d = p.model_dump(exclude_unset=True)
    if (
        "recommended_semester_id" in d
        and d["recommended_semester_id"]
    ):
        get_or_404(
            db,
            Semester,
            d["recommended_semester_id"],
            "Semester",
        )
    for k, v in d.items():
        setattr(x, k, v)
    commit(db)
    db.refresh(x)
    return x
def remove_curriculum(db: Session, i: UUID):
    x = get_or_404(
        db,
        ProgramCourse,
        i,
        "Curriculum entry",
    )
    db.delete(x)
    commit(db)
# ============================================================
# COURSE OFFERINGS
# ============================================================
def validate_offering_relations(db: Session, d):
    course = get_or_404(
        db,
        Course,
        d["course_id"],
        "Course",
    )
    section = get_or_404(
        db,
        Section,
        d["section_id"],
        "Section",
    )
    sess = get_or_404(
        db,
        AcademicSession,
        d["academic_session_id"],
        "Academic session",
    )
    sem = get_or_404(
        db,
        Semester,
        d["semester_id"],
        "Semester",
    )
    if sem.academic_session_id != sess.id:
        raise HTTPException(
            status_code=400,
            detail="Semester does not belong to the academic session",
        )
    if section.semester_id != sem.id:
        raise HTTPException(
            status_code=400,
            detail="Section does not belong to the selected semester",
        )
    if (
        section.course_id is not None
        and section.course_id != course.id
    ):
        raise HTTPException(
            status_code=400,
            detail="Section is already associated with a different legacy course",
        )
    if d.get("teacher_id") is not None:
        get_or_404(
            db,
            Teacher,
            d["teacher_id"],
            "Teacher",
        )
    if (
        not course.is_active
        or not section.is_active
        or not sess.is_active
        or not sem.is_active
    ):
        raise HTTPException(
            status_code=400,
            detail="Course, section, session and semester must be active",
        )
    return course, section, sess, sem
def create_offering(db: Session, p):
    d = p.model_dump()
    validate_offering_relations(
        db,
        d,
    )
    x = CourseOffering(
        organization_id=oid(db),
        **d,
    )
    db.add(x)
    commit(db)
    db.refresh(x)
    return x
def update_offering(db: Session, i: UUID, p):
    x = get_or_404(
        db,
        CourseOffering,
        i,
        "Course offering",
    )
    d = p.model_dump(exclude_unset=True)
    merged = {
        k: getattr(x, k)
        for k in [
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
            k: v
            for k, v in d.items()
            if k != "is_active"
        }
    )
    validate_offering_relations(
        db,
        merged,
    )
    for k, v in d.items():
        setattr(x, k, v)
    commit(db)
    db.refresh(x)
    return x
def archive_offering(db: Session, i: UUID):
    x = get_or_404(
        db,
        CourseOffering,
        i,
        "Course offering",
    )
    x.is_active = False
    commit(db)
# ============================================================
# OFFERINGS FOR CURRENT USER
# ============================================================
def list_offerings_for_user(db: Session, user):
    # --------------------------------------------------------
    # TEACHER
    # --------------------------------------------------------
    if user.role.value == "teacher":
        teacher = db.scalar(
            select(Teacher).where(
                Teacher.organization_id == oid(db),
                Teacher.user_id == user.id,
                Teacher.status == "active",
            )
        )
        if teacher is None:
            return []
        return list(
            db.scalars(
                select(CourseOffering)
                .where(
                    CourseOffering.organization_id == oid(db),
                    CourseOffering.teacher_id == teacher.id,
                    CourseOffering.is_active.is_(True),
                )
                .order_by(
                    CourseOffering.created_at.desc()
                )
            ).all()
        )
    # --------------------------------------------------------
    # ADMIN / OTHER ROLES
    # --------------------------------------------------------
    if user.role.value != "student":
        return list_scoped(
            db,
            CourseOffering,
        )
    # --------------------------------------------------------
    # STUDENT
    # --------------------------------------------------------
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
                CourseOffering.organization_id == oid(db),
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
# STUDENT
# ============================================================
def _student_for_user(db: Session, user):
    return db.scalar(
        select(Student).where(
            Student.organization_id == oid(db),
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
    # STUDENT ENROLLMENT
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
        sid = student.id
        if (
            p.student_id is not None
            and p.student_id != sid
        ):
            raise HTTPException(
                status_code=403,
                detail="Students may only enroll themselves",
            )
    # --------------------------------------------------------
    # ADMIN ENROLLMENT
    # --------------------------------------------------------
    else:
        if p.student_id is None:
            raise HTTPException(
                status_code=422,
                detail="student_id is required for administrator enrollment",
            )
        sid = p.student_id
    # --------------------------------------------------------
    # VALIDATE STUDENT
    # --------------------------------------------------------
    student = get_or_404(
        db,
        Student,
        sid,
        "Student",
    )
    # --------------------------------------------------------
    # VALIDATE OFFERING
    # --------------------------------------------------------
    offering = db.scalar(
        select(CourseOffering)
        .where(
            CourseOffering.organization_id == oid(db),
            CourseOffering.id == p.course_offering_id,
        )
        .with_for_update()
    )
    if offering is None:
        fail("Course offering")
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
    # --------------------------------------------------------
    # VALIDATE SECTION
    # --------------------------------------------------------
    section = get_or_404(
        db,
        Section,
        offering.section_id,
        "Section",
    )
    if student.program_id != section.program_id:
        raise HTTPException(
            status_code=400,
            detail="Student program does not match the course offering section",
        )
    if (
        student.academic_session_id
        != offering.academic_session_id
    ):
        raise HTTPException(
            status_code=400,
            detail="Student academic session does not match the offering",
        )
    # --------------------------------------------------------
    # CHECK DUPLICATE
    # --------------------------------------------------------
    existing = db.scalar(
        select(Enrollment).where(
            Enrollment.organization_id == oid(db),
            Enrollment.student_id == sid,
            Enrollment.course_offering_id
            == offering.id,
        )
    )
    if existing:
        raise HTTPException(
            status_code=409,
            detail="Student is already enrolled in this course offering",
        )
    # --------------------------------------------------------
    # CHECK CAPACITY
    # --------------------------------------------------------
    if offering.max_students is not None:
        count = (
            db.scalar(
                select(func.count())
                .select_from(Enrollment)
                .where(
                    Enrollment.organization_id == oid(db),
                    Enrollment.course_offering_id
                    == offering.id,
                    Enrollment.status
                    == EnrollmentStatus.ENROLLED,
                )
            )
            or 0
        )
        if count >= offering.max_students:
            raise HTTPException(
                status_code=409,
                detail="Course offering capacity has been reached",
            )
    # --------------------------------------------------------
    # CREATE ENROLLMENT
    # --------------------------------------------------------
    x = Enrollment(
        organization_id=oid(db),
        student_id=sid,
        course_offering_id=offering.id,
    )
    db.add(x)
    commit(db)
    db.refresh(x)
    return x
def list_enrollments(
    db: Session,
    student_id: UUID | None = None,
    offering_id: UUID | None = None,
):
    stmt = select(Enrollment).where(
        Enrollment.organization_id == oid(db)
    )
    if student_id:
        stmt = stmt.where(
            Enrollment.student_id == student_id
        )
    if offering_id:
        stmt = stmt.where(
            Enrollment.course_offering_id
            == offering_id
        )
    return list(
        db.scalars(
            stmt.order_by(
                Enrollment.created_at.desc()
            )
        ).all()
    )
def get_enrollment(db: Session, i: UUID):
    return get_or_404(
        db,
        Enrollment,
        i,
        "Enrollment",
    )
def update_enrollment(db: Session, i: UUID, p):
    x = get_enrollment(
        db,
        i,
    )
    x.status = p.status
    x.dropped_at = (
        datetime.now(timezone.utc)
        if p.status
        in {
            EnrollmentStatus.DROPPED,
            EnrollmentStatus.WITHDRAWN,
        }
        else None
    )
    commit(db)
    db.refresh(x)
    return x
