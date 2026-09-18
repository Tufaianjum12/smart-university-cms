from datetime import datetime
from decimal import Decimal
from uuid import UUID
from pydantic import BaseModel, ConfigDict, Field, model_validator
from app.models.academic import CourseType, EnrollmentStatus

class CourseCreate(BaseModel):
    department_id: UUID
    course_code: str = Field(min_length=2, max_length=40)
    title: str = Field(min_length=2, max_length=200)
    description: str | None = Field(None, max_length=5000)
    credit_hours: Decimal = Field(gt=0, le=20, decimal_places=2)
    course_type: CourseType = CourseType.THEORY

class CourseUpdate(BaseModel):
    department_id: UUID | None = None
    course_code: str | None = Field(None, min_length=2, max_length=40)
    title: str | None = Field(None, min_length=2, max_length=200)
    description: str | None = Field(None, max_length=5000)
    credit_hours: Decimal | None = Field(None, gt=0, le=20, decimal_places=2)
    course_type: CourseType | None = None
    is_active: bool | None = None

class CourseRead(CourseCreate):
    id: UUID
    organization_id: UUID
    is_active: bool
    created_at: datetime
    updated_at: datetime
    model_config = ConfigDict(from_attributes=True)

class PrerequisiteCreate(BaseModel):
    prerequisite_course_id: UUID

class PrerequisiteRead(BaseModel):
    id: UUID
    organization_id: UUID
    course_id: UUID
    prerequisite_course_id: UUID
    created_at: datetime
    updated_at: datetime
    model_config = ConfigDict(from_attributes=True)

class CurriculumCreate(BaseModel):
    course_id: UUID
    recommended_semester_id: UUID | None = None
    is_required: bool = True
    sort_order: int = Field(default=0, ge=0)

class CurriculumUpdate(BaseModel):
    recommended_semester_id: UUID | None = None
    is_required: bool | None = None
    sort_order: int | None = Field(None, ge=0)

class CurriculumRead(BaseModel):
    id: UUID
    organization_id: UUID
    program_id: UUID
    course_id: UUID
    recommended_semester_id: UUID | None
    is_required: bool
    sort_order: int
    created_at: datetime
    updated_at: datetime
    model_config = ConfigDict(from_attributes=True)

class OfferingCreate(BaseModel):
    course_id: UUID
    section_id: UUID
    academic_session_id: UUID
    semester_id: UUID
    teacher_id: UUID | None = None
    max_students: int | None = Field(None, gt=0, le=100000)

class OfferingUpdate(BaseModel):
    course_id: UUID | None = None
    section_id: UUID | None = None
    academic_session_id: UUID | None = None
    semester_id: UUID | None = None
    teacher_id: UUID | None = None
    max_students: int | None = Field(None, gt=0, le=100000)
    is_active: bool | None = None

class OfferingRead(OfferingCreate):
    id: UUID
    organization_id: UUID
    is_active: bool
    created_at: datetime
    updated_at: datetime
    model_config = ConfigDict(from_attributes=True)

class EnrollmentCreate(BaseModel):
    student_id: UUID | None = None
    course_offering_id: UUID

class EnrollmentStatusUpdate(BaseModel):
    status: EnrollmentStatus

class EnrollmentRead(BaseModel):
    id: UUID
    organization_id: UUID
    student_id: UUID
    course_offering_id: UUID
    enrolled_at: datetime
    dropped_at: datetime | None
    status: EnrollmentStatus
    created_at: datetime
    updated_at: datetime
    model_config = ConfigDict(from_attributes=True)
