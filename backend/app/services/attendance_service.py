from __future__ import annotations

from datetime import date
from decimal import Decimal, ROUND_HALF_UP
from uuid import UUID

from fastapi import HTTPException
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models import (
    AcademicStatus,
    AttendanceRecord,
    AttendanceSession,
    CourseOffering,
    Enrollment,
    EnrollmentStatus,
    Student,
    Teacher,
)
from app.models.user import User, UserRole

from app.models.academic import AttendanceStatus as AttendanceStatusEnum
from app.schemas.attendance import (
    AttendanceSessionCreate,
    AttendanceSessionUpdate,
    BulkAttendanceCreate,
    AttendanceRecordUpdate,
    AttendanceSessionStatus,
)


def calculate_attendance_percentage(
    present: int,
    absent: int,
    late: int,
    excused: int = 0,
    *,
    late_counts_as_attended: bool = True,
    excused_counts_in_denominator: bool = False,
) -> Decimal:
    attended = present + (late if late_counts_as_attended else 0)
    counted = present + absent + late

    if excused_counts_in_denominator:
        counted += excused

    if counted == 0:
        return Decimal("0.00")

    return (
        Decimal(attended) * Decimal("100") / Decimal(counted)
    ).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def oid(user: User) -> UUID:
    if user.organization_id is None:
        raise HTTPException(403, "Organization membership required")

    return user.organization_id


def get_session_or_404(
    db: Session,
    session_id: UUID,
    user: User,
) -> AttendanceSession:
    obj = db.scalar(
        select(AttendanceSession).where(
            AttendanceSession.organization_id == oid(user),
            AttendanceSession.id == session_id,
        )
    )

    if obj is None:
        raise HTTPException(404, "Attendance session not found")

    return obj


def get_record_or_404(
    db: Session,
    record_id: UUID,
    user: User,
) -> AttendanceRecord:
    obj = db.scalar(
        select(AttendanceRecord).where(
            AttendanceRecord.organization_id == oid(user),
            AttendanceRecord.id == record_id,
        )
    )

    if obj is None:
        raise HTTPException(404, "Attendance record not found")

    return obj


def _teacher_can_manage(
    db: Session,
    user: User,
    offering: CourseOffering,
) -> bool:
    if user.role in {
        UserRole.UNIVERSITY_ADMIN,
        UserRole.DEPARTMENT_ADMIN,
    }:
        return True

    if user.role != UserRole.TEACHER:
        return False

    return (
        db.scalar(
            select(Teacher.id).where(
                Teacher.organization_id == oid(user),
                Teacher.id == offering.teacher_id,
                Teacher.user_id == user.id,
                Teacher.status == AcademicStatus.ACTIVE,
            )
        )
        is not None
    )


def _ensure_manage_access(
    db: Session,
    user: User,
    offering: CourseOffering,
) -> None:
    if not _teacher_can_manage(db, user, offering):
        raise HTTPException(
            403,
            "You are not authorized to manage attendance for this course offering",
        )


def _offering(
    db: Session,
    offering_id: UUID,
    user: User,
) -> CourseOffering:
    obj = db.scalar(
        select(CourseOffering).where(
            CourseOffering.organization_id == oid(user),
            CourseOffering.id == offering_id,
        )
    )

    if obj is None:
        raise HTTPException(404, "Course offering not found")

    return obj


def create_session(
    db: Session,
    payload: AttendanceSessionCreate,
    user: User,
) -> AttendanceSession:
    offering = _offering(db, payload.course_offering_id, user)

    if not offering.is_active:
        raise HTTPException(400, "Course offering is not active")

    _ensure_manage_access(db, user, offering)

    obj = AttendanceSession(
        organization_id=oid(user),
        course_offering_id=payload.course_offering_id,
        session_date=payload.session_date,
        start_time=payload.start_time,
        end_time=payload.end_time,
        topic=payload.topic,
        notes=payload.notes,
        status=payload.status,
        created_by_user_id=user.id,
    )

    db.add(obj)

    try:
        db.commit()
    except Exception as exc:
        db.rollback()

        from sqlalchemy.exc import IntegrityError

        if isinstance(exc, IntegrityError):
            raise HTTPException(
                409,
                "An attendance session already exists for this offering, date and start time",
            ) from exc

        raise

    db.refresh(obj)

    return obj


def list_sessions(
    db: Session,
    user: User,
    offering_id: UUID | None = None,
    session_date: date | None = None,
):
    stmt = select(AttendanceSession).where(
        AttendanceSession.organization_id == oid(user)
    )

    if offering_id is not None:
        offering = _offering(db, offering_id, user)

        if user.role == UserRole.TEACHER:
            _ensure_manage_access(db, user, offering)

        elif user.role == UserRole.STUDENT:
            raise HTTPException(
                403,
                "Students may only view their own attendance",
            )

        elif user.role not in {
            UserRole.UNIVERSITY_ADMIN,
            UserRole.DEPARTMENT_ADMIN,
        }:
            raise HTTPException(403, "Attendance access required")

        stmt = stmt.where(
            AttendanceSession.course_offering_id == offering_id
        )

    elif user.role == UserRole.TEACHER:
        teacher = db.scalar(
            select(Teacher).where(
                Teacher.organization_id == oid(user),
                Teacher.user_id == user.id,
            )
        )

        if teacher is None:
            return []

        stmt = (
            stmt.join(
                CourseOffering,
                CourseOffering.id == AttendanceSession.course_offering_id,
            )
            .where(
                CourseOffering.organization_id == oid(user),
                CourseOffering.teacher_id == teacher.id,
            )
        )

    elif user.role not in {
        UserRole.UNIVERSITY_ADMIN,
        UserRole.DEPARTMENT_ADMIN,
    }:
        raise HTTPException(403, "Attendance access required")

    if session_date is not None:
        stmt = stmt.where(
            AttendanceSession.session_date == session_date
        )

    return list(
        db.scalars(
            stmt.order_by(
                AttendanceSession.session_date.desc(),
                AttendanceSession.created_at.desc(),
            )
        ).all()
    )


def get_session(
    db: Session,
    session_id: UUID,
    user: User,
) -> AttendanceSession:
    obj = get_session_or_404(db, session_id, user)

    offering = _offering(db, obj.course_offering_id, user)

    _ensure_manage_access(db, user, offering)

    return obj


def update_session(
    db: Session,
    session_id: UUID,
    payload: AttendanceSessionUpdate,
    user: User,
) -> AttendanceSession:
    obj = get_session_or_404(db, session_id, user)

    offering = _offering(db, obj.course_offering_id, user)

    _ensure_manage_access(db, user, offering)

    data = payload.model_dump(exclude_unset=True)

    merged_date = data.get("session_date", obj.session_date)
    merged_start = data.get("start_time", obj.start_time)
    merged_end = data.get("end_time", obj.end_time)

    if merged_start and merged_end and merged_end <= merged_start:
        raise HTTPException(
            400,
            "end_time must be after start_time",
        )

    if (
        obj.status == AttendanceSessionStatus.COMPLETED
        and user.role == UserRole.TEACHER
    ):
        raise HTTPException(
            403,
            "Teachers cannot edit completed attendance sessions",
        )

    for key, value in data.items():
        setattr(obj, key, value)

    try:
        db.commit()
    except Exception as exc:
        db.rollback()

        from sqlalchemy.exc import IntegrityError

        if isinstance(exc, IntegrityError):
            raise HTTPException(
                409,
                "Attendance session conflicts with an existing session",
            ) from exc

        raise

    db.refresh(obj)

    return obj


def list_enrollments_for_session(
    db: Session,
    session_id: UUID,
    user: User,
):
    obj = get_session(db, session_id, user)

    rows = db.execute(
        select(Enrollment, Student, User)
        .join(Student, Student.id == Enrollment.student_id)
        .outerjoin(
            User,
            (User.organization_id == Student.organization_id)
            & (User.id == Student.user_id),
        )
        .where(
            Enrollment.organization_id == oid(user),
            Enrollment.course_offering_id == obj.course_offering_id,
            Enrollment.status == EnrollmentStatus.ENROLLED,
            Student.organization_id == oid(user),
        )
        .order_by(Student.student_number)
    ).all()

    return [
        {
            "enrollment_id": enrollment.id,
            "student_id": student.id,
            "student_number": student.student_number,
            "student_name": db_user.full_name if db_user else None,
            "status": enrollment.status.value,
        }
        for enrollment, student, db_user in rows
    ]


def bulk_mark(
    db: Session,
    session_id: UUID,
    payload: BulkAttendanceCreate,
    user: User,
):
    obj = get_session_or_404(db, session_id, user)

    offering = _offering(db, obj.course_offering_id, user)

    _ensure_manage_access(db, user, offering)

    if obj.status == AttendanceSessionStatus.CANCELLED:
        raise HTTPException(
            400,
            "Cancelled sessions cannot receive attendance",
        )

    if (
        obj.status == AttendanceSessionStatus.COMPLETED
        and user.role == UserRole.TEACHER
    ):
        raise HTTPException(
            403,
            "Teachers cannot modify completed attendance sessions",
        )

    enrollment_ids = [
        item.enrollment_id for item in payload.records
    ]

    if len(enrollment_ids) != len(set(enrollment_ids)):
        raise HTTPException(
            400,
            "Duplicate enrollment IDs in bulk attendance",
        )

    enrollments = {
        e.id: e
        for e in db.scalars(
            select(Enrollment).where(
                Enrollment.organization_id == oid(user),
                Enrollment.id.in_(enrollment_ids),
                Enrollment.course_offering_id == obj.course_offering_id,
            )
        ).all()
    }

    if len(enrollments) != len(enrollment_ids):
        raise HTTPException(
            400,
            "Every enrollment must belong to this tenant and course offering",
        )

    if any(
        e.status != EnrollmentStatus.ENROLLED
        for e in enrollments.values()
    ):
        raise HTTPException(
            400,
            "Attendance can only be marked for active enrollments",
        )

    existing = set(
        db.scalars(
            select(AttendanceRecord.enrollment_id).where(
                AttendanceRecord.organization_id == oid(user),
                AttendanceRecord.attendance_session_id == session_id,
                AttendanceRecord.enrollment_id.in_(enrollment_ids),
            )
        ).all()
    )

    if existing:
        raise HTTPException(
            409,
            "Attendance already exists for one or more submitted enrollments",
        )

    for item in payload.records:
        db.add(
            AttendanceRecord(
                organization_id=oid(user),
                attendance_session_id=session_id,
                enrollment_id=item.enrollment_id,
                status=item.status,
                remarks=item.remarks,
                marked_by_user_id=user.id,
            )
        )

    try:
        db.commit()
    except Exception as exc:
        db.rollback()

        from sqlalchemy.exc import IntegrityError

        if isinstance(exc, IntegrityError):
            raise HTTPException(
                409,
                "Duplicate attendance record or database constraint violation",
            ) from exc

        raise

    return list(
        db.scalars(
            select(AttendanceRecord)
            .where(
                AttendanceRecord.organization_id == oid(user),
                AttendanceRecord.attendance_session_id == session_id,
            )
            .order_by(AttendanceRecord.created_at)
        ).all()
    )


def list_records(
    db: Session,
    session_id: UUID,
    user: User,
):
    obj = get_session_or_404(db, session_id, user)

    offering = _offering(db, obj.course_offering_id, user)

    _ensure_manage_access(db, user, offering)

    return list(
        db.scalars(
            select(AttendanceRecord)
            .where(
                AttendanceRecord.organization_id == oid(user),
                AttendanceRecord.attendance_session_id == session_id,
            )
            .order_by(AttendanceRecord.created_at)
        ).all()
    )


def update_record(
    db: Session,
    record_id: UUID,
    payload: AttendanceRecordUpdate,
    user: User,
):
    record = get_record_or_404(db, record_id, user)

    session = get_session_or_404(
        db,
        record.attendance_session_id,
        user,
    )

    offering = _offering(
        db,
        session.course_offering_id,
        user,
    )

    _ensure_manage_access(db, user, offering)

    if (
        session.status == AttendanceSessionStatus.COMPLETED
        and user.role == UserRole.TEACHER
    ):
        raise HTTPException(
            403,
            "Teachers cannot modify completed attendance sessions",
        )

    record.status = payload.status
    record.remarks = payload.remarks
    record.marked_by_user_id = user.id

    db.commit()
    db.refresh(record)

    return record


def _student_for_user(
    db: Session,
    user: User,
) -> Student | None:
    return db.scalar(
        select(Student).where(
            Student.organization_id == oid(user),
            Student.user_id == user.id,
        )
    )


def student_history(
    db: Session,
    user: User,
    offering_id: UUID | None = None,
):
    student = _student_for_user(db, user)

    if student is None:
        raise HTTPException(
            403,
            "Student profile is required",
        )

    stmt = (
        select(AttendanceRecord, AttendanceSession)
        .join(
            AttendanceSession,
            AttendanceSession.id
            == AttendanceRecord.attendance_session_id,
        )
        .join(
            Enrollment,
            Enrollment.id == AttendanceRecord.enrollment_id,
        )
        .where(
            AttendanceRecord.organization_id == oid(user),
            Enrollment.organization_id == oid(user),
            Enrollment.student_id == student.id,
            AttendanceSession.organization_id == oid(user),
            AttendanceSession.status
            != AttendanceSessionStatus.CANCELLED,
        )
    )

    if offering_id is not None:
        stmt = stmt.where(
            AttendanceSession.course_offering_id == offering_id
        )

    rows = db.execute(
        stmt.order_by(
            AttendanceSession.session_date.desc(),
            AttendanceSession.created_at.desc(),
        )
    ).all()

    return [
        {
            "attendance_session_id": record.attendance_session_id,
            "course_offering_id": session.course_offering_id,
            "session_date": session.session_date,
            "topic": session.topic,
            "status": record.status,
            "remarks": record.remarks,
        }
        for record, session in rows
    ]


def student_summary(
    db: Session,
    user: User,
    offering_id: UUID,
) -> dict:
    student = _student_for_user(db, user)

    if student is None:
        raise HTTPException(
            403,
            "Student profile is required",
        )

    enrolled = db.scalar(
        select(Enrollment).where(
            Enrollment.organization_id == oid(user),
            Enrollment.student_id == student.id,
            Enrollment.course_offering_id == offering_id,
            Enrollment.status.in_(
                [
                    EnrollmentStatus.ENROLLED,
                    EnrollmentStatus.COMPLETED,
                ]
            ),
        )
    )

    if enrolled is None:
        raise HTTPException(
            403,
            "You are not enrolled in this course offering",
        )

    counts = {
        status: count
        for status, count in db.execute(
            select(
                AttendanceRecord.status,
                func.count(AttendanceRecord.id),
            )
            .join(
                AttendanceSession,
                AttendanceSession.id
                == AttendanceRecord.attendance_session_id,
            )
            .where(
                AttendanceRecord.organization_id == oid(user),
                AttendanceRecord.enrollment_id == enrolled.id,
                AttendanceSession.organization_id == oid(user),
                AttendanceSession.course_offering_id == offering_id,
                AttendanceSession.status
                != AttendanceSessionStatus.CANCELLED,
            )
            .group_by(AttendanceRecord.status)
        ).all()
    }

    total_sessions = (
        db.scalar(
            select(func.count(AttendanceSession.id)).where(
                AttendanceSession.organization_id == oid(user),
                AttendanceSession.course_offering_id == offering_id,
                AttendanceSession.status
                != AttendanceSessionStatus.CANCELLED,
            )
        )
        or 0
    )

    present = counts.get(
        AttendanceStatusEnum.PRESENT,
        0,
    )

    absent = counts.get(
        AttendanceStatusEnum.ABSENT,
        0,
    )

    late = counts.get(
        AttendanceStatusEnum.LATE,
        0,
    )

    excused = counts.get(
        AttendanceStatusEnum.EXCUSED,
        0,
    )

    from app.services.attendance_analytics_service import get_policy

    policy = get_policy(db, user)

    counted = (
        present
        + absent
        + late
        + (
            excused
            if policy.excused_counts_in_denominator
            else 0
        )
    )

    percentage = calculate_attendance_percentage(
        present,
        absent,
        late,
        excused,
        late_counts_as_attended=policy.late_counts_as_attended,
        excused_counts_in_denominator=policy.excused_counts_in_denominator,
    )

    return {
        "course_offering_id": offering_id,
        "total_sessions": total_sessions,
        "counted_sessions": counted,
        "present": present,
        "absent": absent,
        "late": late,
        "excused": excused,
        "attendance_percentage": percentage,
        "calculation_rule": (
            f"PRESENT counts as attended; LATE is "
            f"{'attended' if policy.late_counts_as_attended else 'not attended'}; "
            f"EXCUSED is "
            f"{'included' if policy.excused_counts_in_denominator else 'excluded'} "
            f"from the denominator; CANCELLED sessions are excluded."
        ),
    }


def offering_summary(
    db: Session,
    user: User,
    offering_id: UUID,
) -> dict:
    offering = _offering(db, offering_id, user)

    _ensure_manage_access(db, user, offering)

    total_sessions = (
        db.scalar(
            select(func.count(AttendanceSession.id)).where(
                AttendanceSession.organization_id == oid(user),
                AttendanceSession.course_offering_id == offering_id,
                AttendanceSession.status
                != AttendanceSessionStatus.CANCELLED,
            )
        )
        or 0
    )

    rows = db.execute(
        select(
            AttendanceRecord.status,
            func.count(AttendanceRecord.id),
        )
        .join(
            AttendanceSession,
            AttendanceSession.id
            == AttendanceRecord.attendance_session_id,
        )
        .where(
            AttendanceRecord.organization_id == oid(user),
            AttendanceSession.organization_id == oid(user),
            AttendanceSession.course_offering_id == offering_id,
            AttendanceSession.status
            != AttendanceSessionStatus.CANCELLED,
        )
        .group_by(AttendanceRecord.status)
    ).all()

    counts = dict(rows)

    present = counts.get(
        AttendanceStatusEnum.PRESENT,
        0,
    )

    absent = counts.get(
        AttendanceStatusEnum.ABSENT,
        0,
    )

    late = counts.get(
        AttendanceStatusEnum.LATE,
        0,
    )

    excused = counts.get(
        AttendanceStatusEnum.EXCUSED,
        0,
    )

    from app.services.attendance_analytics_service import get_policy

    policy = get_policy(db, user)

    counted = (
        present
        + absent
        + late
        + (
            excused
            if policy.excused_counts_in_denominator
            else 0
        )
    )

    percentage = calculate_attendance_percentage(
        present,
        absent,
        late,
        excused,
        late_counts_as_attended=policy.late_counts_as_attended,
        excused_counts_in_denominator=policy.excused_counts_in_denominator,
    )

    return {
        "course_offering_id": offering_id,
        "total_sessions": total_sessions,
        "counted_sessions": counted,
        "present": present,
        "absent": absent,
        "late": late,
        "excused": excused,
        "attendance_percentage": percentage,
        "calculation_rule": (
            f"PRESENT counts as attended; LATE is "
            f"{'attended' if policy.late_counts_as_attended else 'not attended'}; "
            f"EXCUSED is "
            f"{'included' if policy.excused_counts_in_denominator else 'excluded'} "
            f"from the denominator; CANCELLED sessions are excluded."
        ),
    }
