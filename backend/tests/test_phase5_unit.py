from decimal import Decimal
from uuid import uuid4
import pytest
from pydantic import ValidationError
from app.schemas.course import CourseCreate, EnrollmentCreate, OfferingCreate


def test_course_validation_rejects_non_positive_credit_hours():
    with pytest.raises(ValidationError):
        CourseCreate(department_id=uuid4(), course_code='CS-101', title='Test', credit_hours=Decimal('0'), course_type='core')


def test_enrollment_can_derive_student_for_self_enrollment():
    item = EnrollmentCreate(course_offering_id=uuid4())
    assert item.student_id is None


def test_offering_capacity_must_be_positive():
    with pytest.raises(ValidationError):
        OfferingCreate(course_id=uuid4(), section_id=uuid4(), academic_session_id=uuid4(), semester_id=uuid4(), max_students=0)


def test_course_types_are_structured():
    item = CourseCreate(department_id=uuid4(), course_code='SE-101', title='Programming', credit_hours=3, course_type='lab')
    assert item.course_type.value == 'lab'
