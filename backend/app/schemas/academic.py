from datetime import date, datetime, time
from decimal import Decimal
from uuid import UUID
from pydantic import BaseModel, ConfigDict, Field
from app.models.academic import AcademicStatus, EnrollmentStatus, AttendanceStatus, AssessmentType, NotificationType, TargetType


class TenantRead(BaseModel):
    id: UUID
    organization_id: UUID
    created_at: datetime
    updated_at: datetime
    model_config = ConfigDict(from_attributes=True)

class StudentRead(TenantRead):
    user_id: UUID | None
    student_number: str
    program_id: UUID
    academic_session_id: UUID
    admission_date: date | None
    date_of_birth: date | None
    phone: str | None
    status: AcademicStatus

class TeacherRead(TenantRead):
    user_id: UUID | None
    employee_number: str
    department_id: UUID
    phone: str | None
    status: AcademicStatus

class CourseRead(TenantRead):
    department_id: UUID
    course_code: str
    title: str
    description: str | None
    credit_hours: Decimal
    is_active: bool

class EnrollmentRead(TenantRead):
    student_id: UUID
    section_id: UUID
    enrolled_at: datetime
    status: EnrollmentStatus

class AttendanceRead(TenantRead):
    enrollment_id: UUID
    attendance_date: date
    status: AttendanceStatus
    recorded_by_user_id: UUID
    note: str | None

class AssessmentRead(TenantRead):
    section_id: UUID
    name: str
    assessment_type: AssessmentType
    max_marks: Decimal
    due_at: datetime | None

class GradeRead(TenantRead):
    enrollment_id: UUID
    assessment_id: UUID
    marks_obtained: Decimal
    letter_grade: str | None
    grade_point: Decimal | None
