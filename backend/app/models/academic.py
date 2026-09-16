import enum
import uuid
from datetime import date, datetime, time
from decimal import Decimal

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Date,
    DateTime,
    Enum,
    ForeignKeyConstraint,
    Index,
    Integer,
    Numeric,
    String,
    Text,
    Time,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class AcademicStatus(str, enum.Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    GRADUATED = "graduated"
    SUSPENDED = "suspended"
    WITHDRAWN = "withdrawn"


class EnrollmentStatus(str, enum.Enum):
    ENROLLED = "enrolled"
    DROPPED = "dropped"
    COMPLETED = "completed"
    WITHDRAWN = "withdrawn"


class AttendanceStatus(str, enum.Enum):
    PRESENT = "present"
    ABSENT = "absent"
    LATE = "late"
    EXCUSED = "excused"


class AssessmentType(str, enum.Enum):
    ASSIGNMENT = "assignment"
    QUIZ = "quiz"
    MIDTERM = "midterm"
    FINAL = "final"
    PROJECT = "project"
    OTHER = "other"


class NotificationType(str, enum.Enum):
    GENERAL = "general"
    ACADEMIC = "academic"
    ATTENDANCE = "attendance"
    GRADE = "grade"
    SYSTEM = "system"


class TargetType(str, enum.Enum):
    GPA = "gpa"
    CGPA = "cgpa"


class TenantModel(Base):
    __abstract__ = True

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    organization_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        nullable=False,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )


class Campus(TenantModel):
    __tablename__ = "campuses"

    __table_args__ = (
        UniqueConstraint(
            "organization_id",
            "id",
            name="uq_campuses_org_id",
        ),
        ForeignKeyConstraint(
            ["organization_id"],
            ["organizations.id"],
            ondelete="RESTRICT",
        ),
        UniqueConstraint(
            "organization_id",
            "code",
            name="uq_campus_org_code",
        ),
        Index(
            "ix_campuses_org",
            "organization_id",
        ),
    )

    name: Mapped[str] = mapped_column(
        String(160),
        nullable=False,
    )

    code: Mapped[str] = mapped_column(
        String(40),
        nullable=False,
    )

    address: Mapped[str | None] = mapped_column(
        Text,
    )

    is_active: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
    )


class Department(TenantModel):
    __tablename__ = "departments"

    __table_args__ = (
        UniqueConstraint(
            "organization_id",
            "id",
            name="uq_departments_org_id",
        ),
        ForeignKeyConstraint(
            ["organization_id", "campus_id"],
            ["campuses.organization_id", "campuses.id"],
            ondelete="RESTRICT",
        ),
        UniqueConstraint(
            "organization_id",
            "code",
            name="uq_department_org_code",
        ),
        Index(
            "ix_departments_org",
            "organization_id",
        ),
    )

    campus_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        nullable=False,
    )

    name: Mapped[str] = mapped_column(
        String(160),
        nullable=False,
    )

    code: Mapped[str] = mapped_column(
        String(40),
        nullable=False,
    )

    is_active: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
    )


class Program(TenantModel):
    __tablename__ = "programs"

    __table_args__ = (
        UniqueConstraint(
            "organization_id",
            "id",
            name="uq_programs_org_id",
        ),
        ForeignKeyConstraint(
            ["organization_id", "department_id"],
            ["departments.organization_id", "departments.id"],
            ondelete="RESTRICT",
        ),
        UniqueConstraint(
            "organization_id",
            "code",
            name="uq_program_org_code",
        ),
        Index(
            "ix_programs_org_department",
            "organization_id",
            "department_id",
        ),
    )

    department_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        nullable=False,
    )

    name: Mapped[str] = mapped_column(
        String(160),
        nullable=False,
    )

    code: Mapped[str] = mapped_column(
        String(40),
        nullable=False,
    )

    duration_years: Mapped[int | None] = mapped_column(
        Integer,
    )

    is_active: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
    )


class AcademicSession(TenantModel):
    __tablename__ = "academic_sessions"

    __table_args__ = (
        UniqueConstraint(
            "organization_id",
            "id",
            name="uq_academic_sessions_org_id",
        ),
        ForeignKeyConstraint(
            ["organization_id"],
            ["organizations.id"],
            ondelete="RESTRICT",
        ),
        UniqueConstraint(
            "organization_id",
            "code",
            name="uq_session_org_code",
        ),
        CheckConstraint(
            "end_date IS NULL OR start_date IS NULL OR end_date >= start_date",
            name="ck_session_dates",
        ),
        Index(
            "ix_sessions_org",
            "organization_id",
        ),
    )

    code: Mapped[str] = mapped_column(
        String(40),
        nullable=False,
    )

    name: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )

    start_date: Mapped[date | None] = mapped_column(
        Date,
    )

    end_date: Mapped[date | None] = mapped_column(
        Date,
    )

    is_active: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
    )


class Semester(TenantModel):
    __tablename__ = "semesters"

    __table_args__ = (
        UniqueConstraint(
            "organization_id",
            "id",
            name="uq_semesters_org_id",
        ),
        ForeignKeyConstraint(
            ["organization_id", "academic_session_id"],
            [
                "academic_sessions.organization_id",
                "academic_sessions.id",
            ],
            ondelete="RESTRICT",
        ),
        UniqueConstraint(
            "organization_id",
            "academic_session_id",
            "code",
            name="uq_semester_session_code",
        ),
        CheckConstraint(
            "end_date IS NULL OR start_date IS NULL OR end_date >= start_date",
            name="ck_semester_dates",
        ),
        Index(
            "ix_semesters_org_session",
            "organization_id",
            "academic_session_id",
        ),
    )

    academic_session_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        nullable=False,
    )

    code: Mapped[str] = mapped_column(
        String(40),
        nullable=False,
    )

    name: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )

    start_date: Mapped[date | None] = mapped_column(
        Date,
    )

    end_date: Mapped[date | None] = mapped_column(
        Date,
    )

    is_active: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
    )


class Classroom(TenantModel):
    __tablename__ = "classrooms"

    __table_args__ = (
        UniqueConstraint(
            "organization_id",
            "id",
            name="uq_classrooms_org_id",
        ),
        ForeignKeyConstraint(
            ["organization_id", "campus_id"],
            ["campuses.organization_id", "campuses.id"],
            ondelete="RESTRICT",
        ),
        UniqueConstraint(
            "organization_id",
            "campus_id",
            "room_code",
            name="uq_classroom_room",
        ),
        CheckConstraint(
            "capacity > 0",
            name="ck_classroom_capacity_positive",
        ),
        Index(
            "ix_classrooms_org_campus",
            "organization_id",
            "campus_id",
        ),
    )

    campus_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        nullable=False,
    )

    building: Mapped[str | None] = mapped_column(
        String(100),
    )

    room_code: Mapped[str] = mapped_column(
        String(40),
        nullable=False,
    )

    capacity: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )

    is_active: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
    )


class Student(TenantModel):
    __tablename__ = "students"

    __table_args__ = (
        UniqueConstraint(
            "organization_id",
            "id",
            name="uq_students_org_id",
        ),
        ForeignKeyConstraint(
            ["organization_id", "user_id"],
            ["users.organization_id", "users.id"],
            ondelete="RESTRICT",
        ),
        ForeignKeyConstraint(
            ["organization_id", "program_id"],
            ["programs.organization_id", "programs.id"],
            ondelete="RESTRICT",
        ),
        ForeignKeyConstraint(
            ["organization_id", "academic_session_id"],
            [
                "academic_sessions.organization_id",
                "academic_sessions.id",
            ],
            ondelete="RESTRICT",
        ),
        UniqueConstraint(
            "organization_id",
            "student_number",
            name="uq_student_org_number",
        ),
        Index(
            "ix_students_org_program",
            "organization_id",
            "program_id",
        ),
        Index(
            "ix_students_org_user",
            "organization_id",
            "user_id",
        ),
    )

    user_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        nullable=True,
    )

    student_number: Mapped[str] = mapped_column(
        String(60),
        nullable=False,
    )

    program_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        nullable=False,
    )

    academic_session_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        nullable=False,
    )

    admission_date: Mapped[date | None] = mapped_column(
        Date,
    )

    date_of_birth: Mapped[date | None] = mapped_column(
        Date,
    )

    phone: Mapped[str | None] = mapped_column(
        String(40),
    )

    status: Mapped[AcademicStatus] = mapped_column(
        Enum(
            AcademicStatus,
            name="academic_status",
            values_callable=lambda enum_cls: [
                item.value for item in enum_cls
            ],
        ),
        nullable=False,
        default=AcademicStatus.ACTIVE,
    )


class Teacher(TenantModel):
    __tablename__ = "teachers"

    __table_args__ = (
        UniqueConstraint(
            "organization_id",
            "id",
            name="uq_teachers_org_id",
        ),
        ForeignKeyConstraint(
            ["organization_id", "user_id"],
            ["users.organization_id", "users.id"],
            ondelete="RESTRICT",
        ),
        ForeignKeyConstraint(
            ["organization_id", "department_id"],
            ["departments.organization_id", "departments.id"],
            ondelete="RESTRICT",
        ),
        UniqueConstraint(
            "organization_id",
            "employee_number",
            name="uq_teacher_org_employee",
        ),
        Index(
            "ix_teachers_org_department",
            "organization_id",
            "department_id",
        ),
    )

    user_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        nullable=True,
    )

    employee_number: Mapped[str] = mapped_column(
        String(60),
        nullable=False,
    )

    department_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        nullable=False,
    )

    phone: Mapped[str | None] = mapped_column(
        String(40),
    )

    status: Mapped[AcademicStatus] = mapped_column(
        Enum(
            AcademicStatus,
            name="academic_status",
            values_callable=lambda enum_cls: [
                item.value for item in enum_cls
            ],
        ),
        nullable=False,
        default=AcademicStatus.ACTIVE,
    )


class Guardian(TenantModel):
    __tablename__ = "guardians"

    __table_args__ = (
        UniqueConstraint(
            "organization_id",
            "id",
            name="uq_guardians_org_id",
        ),
        ForeignKeyConstraint(
            ["organization_id", "user_id"],
            ["users.organization_id", "users.id"],
            ondelete="RESTRICT",
        ),
        Index(
            "ix_guardians_org_user",
            "organization_id",
            "user_id",
        ),
    )

    user_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        nullable=True,
    )

    phone: Mapped[str | None] = mapped_column(
        String(40),
    )

    relationship_label: Mapped[str | None] = mapped_column(
        String(60),
    )


class StudentGuardian(TenantModel):
    __tablename__ = "student_guardians"

    __table_args__ = (
        UniqueConstraint(
            "organization_id",
            "id",
            name="uq_student_guardians_org_id",
        ),
        ForeignKeyConstraint(
            ["organization_id", "student_id"],
            ["students.organization_id", "students.id"],
            ondelete="CASCADE",
        ),
        ForeignKeyConstraint(
            ["organization_id", "guardian_id"],
            ["guardians.organization_id", "guardians.id"],
            ondelete="CASCADE",
        ),
        UniqueConstraint(
            "organization_id",
            "student_id",
            "guardian_id",
            name="uq_student_guardian",
        ),
        Index(
            "ix_student_guardians_org_student",
            "organization_id",
            "student_id",
        ),
    )

    student_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        nullable=False,
    )

    guardian_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        nullable=False,
    )


class Course(TenantModel):
    __tablename__ = "courses"

    __table_args__ = (
        UniqueConstraint(
            "organization_id",
            "id",
            name="uq_courses_org_id",
        ),
        ForeignKeyConstraint(
            ["organization_id", "department_id"],
            ["departments.organization_id", "departments.id"],
            ondelete="RESTRICT",
        ),
        UniqueConstraint(
            "organization_id",
            "course_code",
            name="uq_course_org_code",
        ),
        CheckConstraint(
            "credit_hours > 0 AND credit_hours <= 20",
            name="ck_course_credit_hours",
        ),
        Index(
            "ix_courses_org_department",
            "organization_id",
            "department_id",
        ),
    )

    department_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        nullable=False,
    )

    course_code: Mapped[str] = mapped_column(
        String(40),
        nullable=False,
    )

    title: Mapped[str] = mapped_column(
        String(200),
        nullable=False,
    )

    description: Mapped[str | None] = mapped_column(
        Text,
    )

    credit_hours: Mapped[Decimal] = mapped_column(
        Numeric(4, 2),
        nullable=False,
    )

    is_active: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
    )


class CoursePrerequisite(TenantModel):
    __tablename__ = "course_prerequisites"

    __table_args__ = (
        UniqueConstraint(
            "organization_id",
            "id",
            name="uq_course_prerequisites_org_id",
        ),
        ForeignKeyConstraint(
            ["organization_id", "course_id"],
            ["courses.organization_id", "courses.id"],
            ondelete="CASCADE",
        ),
        ForeignKeyConstraint(
            ["organization_id", "prerequisite_course_id"],
            ["courses.organization_id", "courses.id"],
            ondelete="RESTRICT",
        ),
        UniqueConstraint(
            "organization_id",
            "course_id",
            "prerequisite_course_id",
            name="uq_course_prerequisite",
        ),
        CheckConstraint(
            "course_id <> prerequisite_course_id",
            name="ck_course_no_self_prerequisite",
        ),
    )

    course_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        nullable=False,
    )

    prerequisite_course_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        nullable=False,
    )


class Section(TenantModel):
    __tablename__ = "sections"

    __table_args__ = (
        UniqueConstraint(
            "organization_id",
            "id",
            name="uq_sections_org_id",
        ),
        ForeignKeyConstraint(
            ["organization_id", "course_id"],
            ["courses.organization_id", "courses.id"],
            ondelete="RESTRICT",
        ),
        ForeignKeyConstraint(
            ["organization_id", "semester_id"],
            ["semesters.organization_id", "semesters.id"],
            ondelete="RESTRICT",
        ),
        ForeignKeyConstraint(
            ["organization_id", "program_id"],
            ["programs.organization_id", "programs.id"],
            ondelete="RESTRICT",
        ),
        UniqueConstraint(
            "organization_id",
            "semester_id",
            "course_id",
            "section_code",
            name="uq_section_offering",
        ),
        CheckConstraint(
            "capacity IS NULL OR capacity > 0",
            name="ck_section_capacity",
        ),
        Index(
            "ix_sections_org_semester",
            "organization_id",
            "semester_id",
        ),
        Index(
            "ix_sections_org_course",
            "organization_id",
            "course_id",
        ),
    )

    course_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        nullable=False,
    )

    semester_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        nullable=False,
    )

    program_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        nullable=True,
    )

    section_code: Mapped[str] = mapped_column(
        String(40),
        nullable=False,
    )

    capacity: Mapped[int | None] = mapped_column(
        Integer,
    )

    is_active: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
    )


class Enrollment(TenantModel):
    __tablename__ = "enrollments"

    __table_args__ = (
        UniqueConstraint(
            "organization_id",
            "id",
            name="uq_enrollments_org_id",
        ),
        ForeignKeyConstraint(
            ["organization_id", "student_id"],
            ["students.organization_id", "students.id"],
            ondelete="RESTRICT",
        ),
        ForeignKeyConstraint(
            ["organization_id", "section_id"],
            ["sections.organization_id", "sections.id"],
            ondelete="RESTRICT",
        ),
        UniqueConstraint(
            "organization_id",
            "student_id",
            "section_id",
            name="uq_enrollment_student_section",
        ),
        Index(
            "ix_enrollments_org_student",
            "organization_id",
            "student_id",
        ),
        Index(
            "ix_enrollments_org_section",
            "organization_id",
            "section_id",
        ),
    )

    student_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        nullable=False,
    )

    section_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        nullable=False,
    )

    enrolled_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

    status: Mapped[EnrollmentStatus] = mapped_column(
        Enum(
            EnrollmentStatus,
            name="enrollment_status",
            values_callable=lambda enum_cls: [
                item.value for item in enum_cls
            ],
        ),
        nullable=False,
        default=EnrollmentStatus.ENROLLED,
    )


class AttendanceRecord(TenantModel):
    __tablename__ = "attendance_records"

    __table_args__ = (
        UniqueConstraint(
            "organization_id",
            "id",
            name="uq_attendance_records_org_id",
        ),
        ForeignKeyConstraint(
            ["organization_id", "enrollment_id"],
            ["enrollments.organization_id", "enrollments.id"],
            ondelete="RESTRICT",
        ),
        ForeignKeyConstraint(
            ["organization_id", "recorded_by_user_id"],
            ["users.organization_id", "users.id"],
            ondelete="RESTRICT",
        ),
        UniqueConstraint(
            "organization_id",
            "enrollment_id",
            "attendance_date",
            name="uq_attendance_enrollment_date",
        ),
        Index(
            "ix_attendance_org_enrollment_date",
            "organization_id",
            "enrollment_id",
            "attendance_date",
        ),
    )

    enrollment_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        nullable=False,
    )

    attendance_date: Mapped[date] = mapped_column(
        Date,
        nullable=False,
    )

    status: Mapped[AttendanceStatus] = mapped_column(
        Enum(
            AttendanceStatus,
            name="attendance_status",
            values_callable=lambda enum_cls: [
                item.value for item in enum_cls
            ],
        ),
        nullable=False,
    )

    recorded_by_user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        nullable=False,
    )

    note: Mapped[str | None] = mapped_column(
        Text,
    )


class Assessment(TenantModel):
    __tablename__ = "assessments"

    __table_args__ = (
        UniqueConstraint(
            "organization_id",
            "id",
            name="uq_assessments_org_id",
        ),
        ForeignKeyConstraint(
            ["organization_id", "section_id"],
            ["sections.organization_id", "sections.id"],
            ondelete="RESTRICT",
        ),
        UniqueConstraint(
            "organization_id",
            "section_id",
            "name",
            name="uq_assessment_section_name",
        ),
        CheckConstraint(
            "max_marks > 0",
            name="ck_assessment_max_marks",
        ),
        Index(
            "ix_assessments_org_section",
            "organization_id",
            "section_id",
        ),
    )

    section_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        nullable=False,
    )

    name: Mapped[str] = mapped_column(
        String(160),
        nullable=False,
    )

    assessment_type: Mapped[AssessmentType] = mapped_column(
        Enum(
            AssessmentType,
            name="assessment_type",
            values_callable=lambda enum_cls: [
                item.value for item in enum_cls
            ],
        ),
        nullable=False,
    )

    max_marks: Mapped[Decimal] = mapped_column(
        Numeric(8, 2),
        nullable=False,
    )

    due_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
    )


class Grade(TenantModel):
    __tablename__ = "grades"

    __table_args__ = (
        UniqueConstraint(
            "organization_id",
            "id",
            name="uq_grades_org_id",
        ),
        ForeignKeyConstraint(
            ["organization_id", "enrollment_id"],
            ["enrollments.organization_id", "enrollments.id"],
            ondelete="RESTRICT",
        ),
        ForeignKeyConstraint(
            ["organization_id", "assessment_id"],
            ["assessments.organization_id", "assessments.id"],
            ondelete="RESTRICT",
        ),
        UniqueConstraint(
            "organization_id",
            "enrollment_id",
            "assessment_id",
            name="uq_grade_enrollment_assessment",
        ),
        CheckConstraint(
            "marks_obtained >= 0",
            name="ck_grade_marks_nonnegative",
        ),
        CheckConstraint(
            "grade_point IS NULL OR grade_point >= 0",
            name="ck_grade_point_nonnegative",
        ),
        Index(
            "ix_grades_org_enrollment",
            "organization_id",
            "enrollment_id",
        ),
    )

    enrollment_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        nullable=False,
    )

    assessment_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        nullable=False,
    )

    marks_obtained: Mapped[Decimal] = mapped_column(
        Numeric(8, 2),
        nullable=False,
    )

    letter_grade: Mapped[str | None] = mapped_column(
        String(8),
    )

    grade_point: Mapped[Decimal | None] = mapped_column(
        Numeric(5, 2),
    )


class TimetableEntry(TenantModel):
    __tablename__ = "timetable_entries"

    __table_args__ = (
        UniqueConstraint(
            "organization_id",
            "id",
            name="uq_timetable_entries_org_id",
        ),
        ForeignKeyConstraint(
            ["organization_id", "section_id"],
            ["sections.organization_id", "sections.id"],
            ondelete="RESTRICT",
        ),
        ForeignKeyConstraint(
            ["organization_id", "teacher_id"],
            ["teachers.organization_id", "teachers.id"],
            ondelete="RESTRICT",
        ),
        ForeignKeyConstraint(
            ["organization_id", "classroom_id"],
            ["classrooms.organization_id", "classrooms.id"],
            ondelete="RESTRICT",
        ),
        CheckConstraint(
            "day_of_week BETWEEN 0 AND 6",
            name="ck_timetable_day",
        ),
        CheckConstraint(
            "end_time > start_time",
            name="ck_timetable_time",
        ),
        Index(
            "ix_timetable_org_section_day",
            "organization_id",
            "section_id",
            "day_of_week",
        ),
        Index(
            "ix_timetable_org_teacher_day",
            "organization_id",
            "teacher_id",
            "day_of_week",
        ),
        Index(
            "ix_timetable_org_classroom_day",
            "organization_id",
            "classroom_id",
            "day_of_week",
        ),
    )

    section_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        nullable=False,
    )

    teacher_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        nullable=True,
    )

    classroom_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        nullable=True,
    )

    day_of_week: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )

    start_time: Mapped[time] = mapped_column(
        Time,
        nullable=False,
    )

    end_time: Mapped[time] = mapped_column(
        Time,
        nullable=False,
    )


class Notification(TenantModel):
    __tablename__ = "notifications"

    __table_args__ = (
        UniqueConstraint(
            "organization_id",
            "id",
            name="uq_notifications_org_id",
        ),
        ForeignKeyConstraint(
            ["organization_id", "recipient_user_id"],
            ["users.organization_id", "users.id"],
            ondelete="RESTRICT",
        ),
        Index(
            "ix_notifications_org_recipient_read",
            "organization_id",
            "recipient_user_id",
            "is_read",
        ),
    )

    recipient_user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        nullable=False,
    )

    notification_type: Mapped[NotificationType] = mapped_column(
        Enum(
            NotificationType,
            name="notification_type",
            values_callable=lambda enum_cls: [
                item.value for item in enum_cls
            ],
        ),
        nullable=False,
    )

    title: Mapped[str] = mapped_column(
        String(200),
        nullable=False,
    )

    message: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    is_read: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
    )


class AcademicTarget(TenantModel):
    __tablename__ = "academic_targets"

    __table_args__ = (
        UniqueConstraint(
            "organization_id",
            "id",
            name="uq_academic_targets_org_id",
        ),
        ForeignKeyConstraint(
            ["organization_id", "student_id"],
            ["students.organization_id", "students.id"],
            ondelete="RESTRICT",
        ),
        ForeignKeyConstraint(
            ["organization_id", "semester_id"],
            ["semesters.organization_id", "semesters.id"],
            ondelete="RESTRICT",
        ),
        CheckConstraint(
            "target_value >= 0 AND target_value <= 4.0",
            name="ck_target_value",
        ),
        Index(
            "ix_targets_org_student",
            "organization_id",
            "student_id",
        ),
    )

    student_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        nullable=False,
    )

    semester_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        nullable=True,
    )

    target_type: Mapped[TargetType] = mapped_column(
        Enum(
            TargetType,
            name="target_type",
            values_callable=lambda enum_cls: [
                item.value for item in enum_cls
            ],
        ),
        nullable=False,
    )

    target_value: Mapped[Decimal] = mapped_column(
        Numeric(4, 2),
        nullable=False,
    )

    note: Mapped[str | None] = mapped_column(
        Text,
    )