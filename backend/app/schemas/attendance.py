from datetime import date, datetime, time
from uuid import UUID
from decimal import Decimal
from pydantic import BaseModel, ConfigDict, Field, model_validator
from app.models.academic import AttendanceStatus, AttendanceSessionStatus


class AttendanceSessionCreate(BaseModel):
    course_offering_id: UUID
    session_date: date
    start_time: time | None = None
    end_time: time | None = None
    topic: str | None = Field(None, max_length=300)
    notes: str | None = Field(None, max_length=5000)
    status: AttendanceSessionStatus = AttendanceSessionStatus.OPEN

    @model_validator(mode="after")
    def validate_times_and_status(self):
        if self.start_time and self.end_time and self.end_time <= self.start_time:
            raise ValueError("end_time must be after start_time")
        if self.status not in {
            AttendanceSessionStatus.DRAFT,
            AttendanceSessionStatus.OPEN,
            AttendanceSessionStatus.COMPLETED,
            AttendanceSessionStatus.CANCELLED,
        }:
            raise ValueError("Invalid attendance session status")
        return self


class AttendanceSessionUpdate(BaseModel):
    session_date: date | None = None
    start_time: time | None = None
    end_time: time | None = None
    topic: str | None = Field(None, max_length=300)
    notes: str | None = Field(None, max_length=5000)
    status: AttendanceSessionStatus | None = None

    @model_validator(mode="after")
    def validate_times_and_status(self):
        if self.start_time and self.end_time and self.end_time <= self.start_time:
            raise ValueError("end_time must be after start_time")
        if self.status is not None and self.status not in {
            AttendanceSessionStatus.DRAFT,
            AttendanceSessionStatus.OPEN,
            AttendanceSessionStatus.COMPLETED,
            AttendanceSessionStatus.CANCELLED,
        }:
            raise ValueError("Invalid attendance session status")
        return self


class AttendanceSessionRead(AttendanceSessionCreate):
    id: UUID
    organization_id: UUID
    created_by_user_id: UUID
    created_at: datetime
    updated_at: datetime
    model_config = ConfigDict(from_attributes=True)


class AttendanceRecordInput(BaseModel):
    enrollment_id: UUID
    status: AttendanceStatus
    remarks: str | None = Field(None, max_length=2000)


class BulkAttendanceCreate(BaseModel):
    records: list[AttendanceRecordInput] = Field(min_length=1, max_length=10000)


class AttendanceRecordRead(BaseModel):
    id: UUID
    organization_id: UUID
    attendance_session_id: UUID
    enrollment_id: UUID
    status: AttendanceStatus
    remarks: str | None
    marked_at: datetime
    marked_by_user_id: UUID
    created_at: datetime
    updated_at: datetime
    model_config = ConfigDict(from_attributes=True)


class AttendanceRecordUpdate(BaseModel):
    status: AttendanceStatus
    remarks: str | None = Field(None, max_length=2000)


class AttendanceSummary(BaseModel):
    course_offering_id: UUID
    total_sessions: int
    counted_sessions: int
    present: int
    absent: int
    late: int
    excused: int
    attendance_percentage: Decimal
    calculation_rule: str


class AttendanceEnrollmentRow(BaseModel):
    enrollment_id: UUID
    student_id: UUID
    student_number: str
    student_name: str | None
    status: str


class StudentAttendanceHistoryRow(BaseModel):
    attendance_session_id: UUID
    course_offering_id: UUID
    session_date: date
    topic: str | None
    status: AttendanceStatus
    remarks: str | None
