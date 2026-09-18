from datetime import date
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models import User, UserRole
from app.schemas.attendance import (
    AttendanceEnrollmentRow,
    AttendanceRecordRead,
    AttendanceRecordUpdate,
    AttendanceSessionCreate,
    AttendanceSessionRead,
    AttendanceSessionUpdate,
    AttendanceSummary,
    StudentAttendanceHistoryRow,
    BulkAttendanceCreate,
)
from app.security.dependencies import get_current_user, require_roles
from app.services import attendance_service as svc

router = APIRouter(prefix="/attendance", tags=["Phase 6 Attendance"])

manage = Depends(
    require_roles(
        UserRole.UNIVERSITY_ADMIN,
        UserRole.DEPARTMENT_ADMIN,
        UserRole.TEACHER,
    )
)


@router.post("/sessions", response_model=AttendanceSessionRead, status_code=201)
def create_session(
    payload: AttendanceSessionCreate,
    db: Session = Depends(get_db),
    user: User = manage,
):
    return svc.create_session(db, payload, user)


@router.get("/sessions", response_model=list[AttendanceSessionRead])
def list_sessions(
    course_offering_id: UUID | None = Query(None),
    session_date: date | None = Query(None),
    db: Session = Depends(get_db),
    user: User = manage,
):
    return svc.list_sessions(db, user, course_offering_id, session_date)


@router.get("/sessions/{session_id}", response_model=AttendanceSessionRead)
def get_session(
    session_id: UUID,
    db: Session = Depends(get_db),
    user: User = manage,
):
    return svc.get_session(db, session_id, user)


@router.patch("/sessions/{session_id}", response_model=AttendanceSessionRead)
def update_session(
    session_id: UUID,
    payload: AttendanceSessionUpdate,
    db: Session = Depends(get_db),
    user: User = manage,
):
    return svc.update_session(db, session_id, payload, user)


@router.get(
    "/sessions/{session_id}/enrollments",
    response_model=list[AttendanceEnrollmentRow],
)
def session_enrollments(
    session_id: UUID,
    db: Session = Depends(get_db),
    user: User = manage,
):
    return svc.list_enrollments_for_session(db, session_id, user)


@router.post(
    "/sessions/{session_id}/records",
    response_model=list[AttendanceRecordRead],
)
def bulk_mark_attendance(
    session_id: UUID,
    payload: BulkAttendanceCreate,
    db: Session = Depends(get_db),
    user: User = manage,
):
    return svc.bulk_mark(db, session_id, payload, user)


@router.get(
    "/sessions/{session_id}/records",
    response_model=list[AttendanceRecordRead],
)
def list_attendance_records(
    session_id: UUID,
    db: Session = Depends(get_db),
    user: User = manage,
):
    return svc.list_records(db, session_id, user)


@router.patch("/records/{record_id}", response_model=AttendanceRecordRead)
def update_attendance_record(
    record_id: UUID,
    payload: AttendanceRecordUpdate,
    db: Session = Depends(get_db),
    user: User = manage,
):
    return svc.update_record(db, record_id, payload, user)


@router.get(
    "/course-offerings/{offering_id}/summary",
    response_model=AttendanceSummary,
)
def course_offering_summary(
    offering_id: UUID,
    db: Session = Depends(get_db),
    user: User = manage,
):
    return svc.offering_summary(db, user, offering_id)


@router.get("/student/me", response_model=list[StudentAttendanceHistoryRow])
def my_attendance_history(
    course_offering_id: UUID | None = Query(None),
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(UserRole.STUDENT)),
):
    return svc.student_history(db, user, course_offering_id)


@router.get("/student/me/{offering_id}", response_model=AttendanceSummary)
def my_attendance(
    offering_id: UUID,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(UserRole.STUDENT)),
):
    return svc.student_summary(db, user, offering_id)
