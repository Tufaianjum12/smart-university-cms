from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal, ROUND_HALF_UP
from typing import Any
from uuid import UUID

from fastapi import HTTPException
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models import (
    AcademicStatus,
    AttendanceRecord,
    AttendanceSession,
    AttendanceStatus,
    AttendanceSessionStatus,
    CourseOffering,
    Enrollment,
    EnrollmentStatus,
    OrganizationSettings,
    Student,
    Teacher,
    User,
)
from app.models.user import UserRole

from app.services.attendance_calculations import (
    calculate_percentage,
    maximum_future_absences,
    recovery_required,
)


DEFAULT_MINIMUM_ATTENDANCE = Decimal("75.00")
DEFAULT_TREND_THRESHOLD = Decimal("5.00")


@dataclass(frozen=True)
class AttendancePolicy:
    minimum_required_percentage: Decimal = DEFAULT_MINIMUM_ATTENDANCE
    late_counts_as_attended: bool = True
    excused_counts_in_denominator: bool = False
    trend_threshold: Decimal = DEFAULT_TREND_THRESHOLD


def _oid(user: User) -> UUID:
    """
    Return the organization ID belonging to the authenticated user.

    Tenant identity must come from the authenticated user's database record.
    It must never come from client-provided input.
    """
    if user.organization_id is None:
        raise HTTPException(
            status_code=403,
            detail="Organization membership required",
        )

    return user.organization_id


def get_policy(db: Session, user: User) -> AttendancePolicy:
    """
    Get attendance policy for the authenticated user's organization.
    """
    settings = db.scalar(
        select(OrganizationSettings).where(
            OrganizationSettings.organization_id == _oid(user)
        )
    )

    minimum = DEFAULT_MINIMUM_ATTENDANCE
    late = True
    excused_denominator = False
    trend_threshold = DEFAULT_TREND_THRESHOLD

    if settings is not None:
        minimum = Decimal(str(settings.minimum_attendance_percentage))

        rules = settings.academic_rules or {}

        late = bool(
            rules.get(
                "late_counts_as_attended",
                True,
            )
        )

        excused_denominator = bool(
            rules.get(
                "excused_counts_in_denominator",
                False,
            )
        )

        trend_threshold = Decimal(
            str(
                rules.get(
                    "attendance_trend_threshold",
                    DEFAULT_TREND_THRESHOLD,
                )
            )
        )

    return AttendancePolicy(
        minimum_required_percentage=minimum,
        late_counts_as_attended=late,
        excused_counts_in_denominator=excused_denominator,
        trend_threshold=trend_threshold,
    )


def _status_counts(
    rows,
    policy: AttendancePolicy,
) -> tuple[int, int, int, int]:
    present = 0
    absent = 0
    late = 0
    excused = 0

    for status, count in rows:
        value = status.value if hasattr(status, "value") else str(status)

        if value == AttendanceStatus.PRESENT.value:
            present += count

        elif value == AttendanceStatus.ABSENT.value:
            absent += count

        elif value == AttendanceStatus.LATE.value:
            late += count

        elif value == AttendanceStatus.EXCUSED.value:
            excused += count

    return present, absent, late, excused


def _summary_from_counts(
    offering_id: UUID,
    present: int,
    absent: int,
    late: int,
    excused: int,
    total_sessions: int,
    policy: AttendancePolicy,
) -> dict[str, Any]:
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

    percentage = calculate_percentage(
        present,
        absent,
        late,
        excused,
        late_counts_as_attended=policy.late_counts_as_attended,
        excused_counts_in_denominator=policy.excused_counts_in_denominator,
    )

    recovery = recovery_required(
        present
        + (
            late
            if policy.late_counts_as_attended
            else 0
        ),
        counted,
        policy.minimum_required_percentage,
    )

    if percentage >= policy.minimum_required_percentage:
        risk = "SAFE"

    elif recovery["is_recoverable"]:
        risk = "AT_RISK"

    else:
        risk = "CRITICAL"

    return {
        "course_offering_id": offering_id,
        "total_sessions": total_sessions,
        "counted_sessions": counted,
        "present": present,
        "absent": absent,
        "late": late,
        "excused": excused,
        "attendance_percentage": percentage,
        "minimum_required_percentage": (
            policy.minimum_required_percentage
        ),
        "risk": risk,
        "calculation_rule": (
            "PRESENT counts as attended; "
            "LATE is "
            f"{'attended' if policy.late_counts_as_attended else 'not attended'}; "
            "EXCUSED is "
            f"{'included' if policy.excused_counts_in_denominator else 'excluded'} "
            "from the denominator; "
            "CANCELLED sessions are excluded."
        ),
        "classes_required_to_recover": recovery["classes_required"],
        "maximum_future_absences": maximum_future_absences(
            present
            + (
                late
                if policy.late_counts_as_attended
                else 0
            ),
            counted,
            policy.minimum_required_percentage,
        )["maximum_future_absences"],
    }


def _student_for_user(
    db: Session,
    user: User,
) -> Student | None:
    """
    Find the student profile belonging to the authenticated user
    inside the authenticated user's organization.
    """
    return db.scalar(
        select(Student).where(
            Student.organization_id == _oid(user),
            Student.user_id == user.id,
        )
    )


def _offering(
    db: Session,
    offering_id: UUID,
    user: User,
) -> CourseOffering:
    """
    Get a course offering only from the authenticated user's organization.
    """
    item = db.scalar(
        select(CourseOffering).where(
            CourseOffering.organization_id == _oid(user),
            CourseOffering.id == offering_id,
        )
    )

    if item is None:
        raise HTTPException(
            status_code=404,
            detail="Course offering not found",
        )

    return item


def _ensure_teacher_or_admin(
    db: Session,
    user: User,
    offering: CourseOffering,
) -> None:
    """
    Verify that the authenticated user can analyze the course offering.
    """

    if user.role in {
        UserRole.UNIVERSITY_ADMIN,
        UserRole.DEPARTMENT_ADMIN,
    }:
        return

    if user.role != UserRole.TEACHER:
        raise HTTPException(
            status_code=403,
            detail="Attendance analytics access required",
        )

    allowed = db.scalar(
        select(Teacher.id).where(
            Teacher.organization_id == _oid(user),
            Teacher.id == offering.teacher_id,
            Teacher.user_id == user.id,
            Teacher.status == AcademicStatus.ACTIVE,
        )
    )

    if allowed is None:
        raise HTTPException(
            status_code=403,
            detail="You are not authorized to analyze this course offering",
        )


def student_summary(
    db: Session,
    user: User,
    offering_id: UUID,
    future_classes_available: int | None = None,
) -> dict[str, Any]:
    """
    Return attendance analytics for the authenticated student.
    """

    student = _student_for_user(db, user)

    if student is None:
        raise HTTPException(
            status_code=403,
            detail="Student profile is required",
        )

    enrollment = db.scalar(
        select(Enrollment).where(
            Enrollment.organization_id == _oid(user),
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

    if enrollment is None:
        raise HTTPException(
            status_code=403,
            detail="You are not enrolled in this course offering",
        )

    policy = get_policy(db, user)

    total_sessions = (
        db.scalar(
            select(func.count(AttendanceSession.id)).where(
                AttendanceSession.organization_id == _oid(user),
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
            AttendanceRecord.organization_id == _oid(user),
            AttendanceRecord.enrollment_id == enrollment.id,
            AttendanceSession.organization_id == _oid(user),
            AttendanceSession.course_offering_id == offering_id,
            AttendanceSession.status
            != AttendanceSessionStatus.CANCELLED,
        )
        .group_by(AttendanceRecord.status)
    ).all()

    present, absent, late, excused = _status_counts(
        rows,
        policy,
    )

    result = _summary_from_counts(
        offering_id,
        present,
        absent,
        late,
        excused,
        total_sessions,
        policy,
    )

    attended = present + (
        late
        if policy.late_counts_as_attended
        else 0
    )

    counted = result["counted_sessions"]

    result["recovery"] = recovery_required(
        attended,
        counted,
        policy.minimum_required_percentage,
        future_classes_available,
    )

    result["maximum_absences"] = maximum_future_absences(
        attended,
        counted,
        policy.minimum_required_percentage,
        future_classes_available,
    )

    return result


def student_trend(
    db: Session,
    user: User,
    offering_id: UUID,
) -> dict[str, Any]:
    """
    Return running attendance trend for the authenticated student.
    """

    student = _student_for_user(db, user)

    if student is None:
        raise HTTPException(
            status_code=403,
            detail="Student profile is required",
        )

    enrollment = db.scalar(
        select(Enrollment).where(
            Enrollment.organization_id == _oid(user),
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

    if enrollment is None:
        raise HTTPException(
            status_code=403,
            detail="You are not enrolled in this course offering",
        )

    policy = get_policy(db, user)

    rows = db.execute(
        select(
            AttendanceRecord,
            AttendanceSession,
        )
        .join(
            AttendanceSession,
            AttendanceSession.id
            == AttendanceRecord.attendance_session_id,
        )
        .where(
            AttendanceRecord.organization_id == _oid(user),
            AttendanceRecord.enrollment_id == enrollment.id,
            AttendanceSession.organization_id == _oid(user),
            AttendanceSession.course_offering_id == offering_id,
            AttendanceSession.status
            != AttendanceSessionStatus.CANCELLED,
        )
        .order_by(
            AttendanceSession.session_date,
            AttendanceSession.created_at,
        )
    ).all()

    points = []
    attended = 0
    counted = 0
    counted_percentages = []

    for record, session in rows:
        value = record.status.value

        if (
            value == AttendanceStatus.EXCUSED.value
            and not policy.excused_counts_in_denominator
        ):
            pass

        else:
            counted += 1

            if (
                value == AttendanceStatus.PRESENT.value
                or (
                    value == AttendanceStatus.LATE.value
                    and policy.late_counts_as_attended
                )
            ):
                attended += 1

        percentage = (
            Decimal(attended)
            * Decimal("100")
            / Decimal(counted)
            if counted
            else Decimal("0")
        )

        percentage = percentage.quantize(
            Decimal("0.01"),
            rounding=ROUND_HALF_UP,
        )

        points.append(
            {
                "date": session.session_date,
                "status": record.status,
                "running_percentage": percentage,
                "attendance_session_id": session.id,
            }
        )

        if counted:
            counted_percentages.append(percentage)

    if len(counted_percentages) < 4:
        classification = "INSUFFICIENT_DATA"

    else:
        midpoint = len(counted_percentages) // 2

        previous = counted_percentages[midpoint - 1]
        recent = counted_percentages[-1]

        difference = recent - previous

        if difference >= policy.trend_threshold:
            classification = "IMPROVING"

        elif difference <= -policy.trend_threshold:
            classification = "DECLINING"

        else:
            classification = "STABLE"

    return {
        "course_offering_id": offering_id,
        "points": points,
        "classification": classification,
        "trend_threshold": policy.trend_threshold,
        "calculation_rule": (
            "Trend compares the latest running attendance "
            "percentage with the running percentage at the "
            "midpoint of the counted attendance history. "
            f"A change of at least {policy.trend_threshold} "
            "percentage points is IMPROVING/DECLINING; "
            "smaller changes are STABLE. Fewer than 4 counted "
            "records is INSUFFICIENT_DATA."
        ),
    }


def course_analytics(
    db: Session,
    user: User,
    offering_id: UUID,
) -> dict[str, Any]:
    """
    Return course-level attendance analytics for an authorized
    administrator or teacher.
    """

    offering = _offering(
        db,
        offering_id,
        user,
    )

    _ensure_teacher_or_admin(
        db,
        user,
        offering,
    )

    policy = get_policy(
        db,
        user,
    )

    enrolled_rows = db.execute(
        select(
            Enrollment.id,
            Enrollment.student_id,
        ).where(
            Enrollment.organization_id == _oid(user),
            Enrollment.course_offering_id == offering_id,
            Enrollment.status.in_(
                [
                    EnrollmentStatus.ENROLLED,
                    EnrollmentStatus.COMPLETED,
                ]
            ),
        )
    ).all()

    enrollment_ids = [
        row.id
        for row in enrolled_rows
    ]

    student_by_enrollment = {
        row.id: row.student_id
        for row in enrolled_rows
    }

    total_sessions = (
        db.scalar(
            select(func.count(AttendanceSession.id)).where(
                AttendanceSession.organization_id == _oid(user),
                AttendanceSession.course_offering_id == offering_id,
                AttendanceSession.status
                != AttendanceSessionStatus.CANCELLED,
            )
        )
        or 0
    )

    if not enrollment_ids:
        return {
            "course_offering_id": offering_id,
            "total_sessions": total_sessions,
            "student_count": 0,
            "course_average_percentage": Decimal("0.00"),
            "safe_count": 0,
            "at_risk_count": 0,
            "critical_count": 0,
            "students": [],
            "minimum_required_percentage": (
                policy.minimum_required_percentage
            ),
        }

    rows = db.execute(
        select(
            AttendanceRecord.enrollment_id,
            AttendanceRecord.status,
            func.count(AttendanceRecord.id),
        ).where(
            AttendanceRecord.organization_id == _oid(user),
            AttendanceRecord.enrollment_id.in_(enrollment_ids),
            AttendanceRecord.attendance_session_id.in_(
                select(AttendanceSession.id).where(
                    AttendanceSession.organization_id == _oid(user),
                    AttendanceSession.course_offering_id == offering_id,
                    AttendanceSession.status
                    != AttendanceSessionStatus.CANCELLED,
                )
            ),
        ).group_by(
            AttendanceRecord.enrollment_id,
            AttendanceRecord.status,
        )
    ).all()

    counts_by_enrollment: dict[
        UUID,
        dict[str, int],
    ] = {
        eid: {
            "present": 0,
            "absent": 0,
            "late": 0,
            "excused": 0,
        }
        for eid in enrollment_ids
    }

    for eid, status, count in rows:
        value = (
            status.value
            if hasattr(status, "value")
            else str(status)
        )

        if value in counts_by_enrollment[eid]:
            counts_by_enrollment[eid][value] = count

    students = []

    for enrollment_id, student_id in student_by_enrollment.items():
        c = counts_by_enrollment[enrollment_id]

        summary = _summary_from_counts(
            offering_id,
            c["present"],
            c["absent"],
            c["late"],
            c["excused"],
            total_sessions,
            policy,
        )

        students.append(
            {
                "enrollment_id": enrollment_id,
                "student_id": student_id,
                "attendance_percentage": (
                    summary["attendance_percentage"]
                ),
                "present": c["present"],
                "absent": c["absent"],
                "late": c["late"],
                "excused": c["excused"],
                "risk": summary["risk"],
                "classes_required_to_recover": (
                    summary["classes_required_to_recover"]
                ),
                "maximum_future_absences": (
                    summary["maximum_future_absences"]
                ),
            }
        )

    average = (
        (
            sum(
                (
                    item["attendance_percentage"]
                    for item in students
                ),
                Decimal("0"),
            )
            / Decimal(len(students))
        ).quantize(
            Decimal("0.01"),
            rounding=ROUND_HALF_UP,
        )
        if students
        else Decimal("0.00")
    )

    safe = sum(
        item["risk"] == "SAFE"
        for item in students
    )

    at_risk = sum(
        item["risk"] == "AT_RISK"
        for item in students
    )

    critical = sum(
        item["risk"] == "CRITICAL"
        for item in students
    )

    return {
        "course_offering_id": offering_id,
        "total_sessions": total_sessions,
        "student_count": len(students),
        "course_average_percentage": average,
        "safe_count": safe,
        "at_risk_count": at_risk,
        "critical_count": critical,
        "students": students,
        "minimum_required_percentage": (
            policy.minimum_required_percentage
        ),
    }

