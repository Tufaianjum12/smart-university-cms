from __future__ import annotations

from datetime import date
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.models.academic import AttendanceStatus


class AttendancePolicyRead(BaseModel):
    minimum_required_percentage: Decimal
    late_counts_as_attended: bool
    excused_counts_in_denominator: bool
    trend_threshold: Decimal
    model_config = ConfigDict(from_attributes=False)


class AttendanceRecoveryRead(BaseModel):
    current_percentage: Decimal
    target_percentage: Decimal
    classes_required: int | None
    future_classes_available: int | None
    is_recoverable: bool


class AttendanceMaximumAbsencesRead(BaseModel):
    current_percentage: Decimal
    target_percentage: Decimal
    maximum_future_absences: int | None
    future_classes_available: int | None
    is_currently_compliant: bool


class StudentAttendanceAnalyticsRead(BaseModel):
    course_offering_id: UUID
    total_sessions: int
    counted_sessions: int
    present: int
    absent: int
    late: int
    excused: int
    attendance_percentage: Decimal
    minimum_required_percentage: Decimal
    risk: str
    calculation_rule: str
    classes_required_to_recover: int | None
    maximum_future_absences: int | None
    recovery: AttendanceRecoveryRead
    maximum_absences: AttendanceMaximumAbsencesRead


class AttendanceTrendPointRead(BaseModel):
    date: date
    status: AttendanceStatus
    running_percentage: Decimal
    attendance_session_id: UUID


class StudentAttendanceTrendRead(BaseModel):
    course_offering_id: UUID
    points: list[AttendanceTrendPointRead]
    classification: str
    trend_threshold: Decimal
    calculation_rule: str


class CourseStudentAnalyticsRead(BaseModel):
    enrollment_id: UUID
    student_id: UUID
    attendance_percentage: Decimal
    present: int
    absent: int
    late: int
    excused: int
    risk: str
    classes_required_to_recover: int | None
    maximum_future_absences: int | None


class CourseAttendanceAnalyticsRead(BaseModel):
    course_offering_id: UUID
    total_sessions: int
    student_count: int
    course_average_percentage: Decimal
    safe_count: int
    at_risk_count: int
    critical_count: int
    students: list[CourseStudentAnalyticsRead]
    minimum_required_percentage: Decimal


class RecoveryQuery(BaseModel):
    attended: int = Field(ge=0)
    counted: int = Field(ge=0)
    target_percentage: Decimal = Field(ge=0, le=100)
    future_classes_available: int | None = Field(None, ge=0)


class MaximumAbsencesQuery(BaseModel):
    attended: int = Field(ge=0)
    counted: int = Field(ge=0)
    target_percentage: Decimal = Field(ge=0, le=100)
    future_classes_available: int | None = Field(None, ge=0)
