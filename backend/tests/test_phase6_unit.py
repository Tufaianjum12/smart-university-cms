from decimal import Decimal
from uuid import uuid4
import pytest
from pydantic import ValidationError

from app.models.academic import AttendanceStatus, AttendanceSessionStatus
from app.schemas.attendance import AttendanceSessionCreate, BulkAttendanceCreate, AttendanceRecordInput
from app.services.attendance_service import calculate_attendance_percentage


def test_attendance_statuses_are_structured():
    assert AttendanceStatus.PRESENT.value == "present"
    assert AttendanceStatus.ABSENT.value == "absent"
    assert AttendanceStatus.LATE.value == "late"
    assert AttendanceStatus.EXCUSED.value == "excused"


def test_session_status_is_structured():
    assert AttendanceSessionStatus.OPEN.value == "open"
    assert AttendanceSessionStatus.COMPLETED.value == "completed"


def test_session_rejects_invalid_time_range():
    with pytest.raises(ValidationError):
        AttendanceSessionCreate(
            course_offering_id=uuid4(),
            session_date="2026-09-18",
            start_time="11:00",
            end_time="10:00",
        )


def test_session_rejects_invalid_status():
    with pytest.raises(ValidationError):
        AttendanceSessionCreate(
            course_offering_id=uuid4(),
            session_date="2026-09-18",
            status="invalid",
        )


def test_bulk_attendance_requires_at_least_one_record():
    with pytest.raises(ValidationError):
        BulkAttendanceCreate(records=[])


def test_attendance_percentage_rule():
    # PRESENT + LATE are attended; ABSENT counts; EXCUSED is excluded.
    assert calculate_attendance_percentage(8, 1, 1) == Decimal("90.00")


def test_zero_counted_sessions_returns_zero():
    assert calculate_attendance_percentage(0, 0, 0) == Decimal("0.00")
