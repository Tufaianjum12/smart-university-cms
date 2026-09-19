from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.user import User, UserRole
from app.schemas.attendance_analytics import (
    AttendanceMaximumAbsencesRead,
    AttendancePolicyRead,
    AttendanceRecoveryRead,
    CourseAttendanceAnalyticsRead,
    StudentAttendanceAnalyticsRead,
    StudentAttendanceTrendRead,
)
from app.security.dependencies import get_current_user, require_roles
from app.services import attendance_analytics_service as svc

router = APIRouter(
    prefix="/attendance/analytics",
    tags=["Phase 7 Attendance Analytics"],
)


@router.get("/policy", response_model=AttendancePolicyRead)
def attendance_policy(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    if user.organization_id is None:
        raise HTTPException(
            status_code=403,
            detail="Organization membership required",
        )

    return svc.get_policy(db, user)


@router.get(
    "/student/me/{offering_id}",
    response_model=StudentAttendanceAnalyticsRead,
)
def my_analytics(
    offering_id: UUID,
    future_classes_available: int | None = Query(None, ge=0),
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(UserRole.STUDENT)),
):
    return svc.student_summary(
        db,
        user,
        offering_id,
        future_classes_available,
    )


@router.get(
    "/student/me/{offering_id}/trend",
    response_model=StudentAttendanceTrendRead,
)
def my_trend(
    offering_id: UUID,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(UserRole.STUDENT)),
):
    return svc.student_trend(db, user, offering_id)


@router.get(
    "/course-offerings/{offering_id}",
    response_model=CourseAttendanceAnalyticsRead,
)
def course_analytics(
    offering_id: UUID,
    db: Session = Depends(get_db),
    user: User = Depends(
        require_roles(
            UserRole.UNIVERSITY_ADMIN,
            UserRole.DEPARTMENT_ADMIN,
            UserRole.TEACHER,
        )
    ),
):
    return svc.course_analytics(db, user, offering_id)


@router.get("/recovery", response_model=AttendanceRecoveryRead)
def recovery(
    attended: int = Query(..., ge=0),
    counted: int = Query(..., ge=0),
    target_percentage: float = Query(..., ge=0, le=100),
    future_classes_available: int | None = Query(None, ge=0),
    _: User = Depends(get_current_user),
):
    if attended > counted:
        raise HTTPException(
            status_code=422,
            detail="attended cannot exceed counted",
        )

    return svc.recovery_required(
        attended,
        counted,
        target_percentage,
        future_classes_available,
    )


@router.get(
    "/maximum-absences",
    response_model=AttendanceMaximumAbsencesRead,
)
def maximum_absences(
    attended: int = Query(..., ge=0),
    counted: int = Query(..., ge=0),
    target_percentage: float = Query(..., ge=0, le=100),
    future_classes_available: int | None = Query(None, ge=0),
    _: User = Depends(get_current_user),
):
    if attended > counted:
        raise HTTPException(
            status_code=422,
            detail="attended cannot exceed counted",
        )

    return svc.maximum_future_absences(
        attended,
        counted,
        target_percentage,
        future_classes_available,
    )