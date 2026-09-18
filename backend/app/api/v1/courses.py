from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.user import User
from app.schemas.academic import StudentRead, TeacherRead
from app.schemas.course import (
    CourseCreate,
    CourseRead,
    CourseUpdate,
    EnrollmentCreate,
    EnrollmentRead,
    EnrollmentStatusUpdate,
    OfferingCreate,
    OfferingRead,
    OfferingUpdate,
)
from app.security.dependencies import get_current_user
from app.services import course_service as svc


router = APIRouter(
    tags=["Courses"],
)


def manager(
    user: User = Depends(get_current_user),
) -> User:
    svc.require_manage(user)
    return user


# ============================================================
# COURSES
# ============================================================

@router.get("/courses", response_model=list[CourseRead])
def list_courses(
    db: Session = Depends(get_db),
    user: User = Depends(manager),
):
    organization_id = svc.require_manage(user)
    return svc.list_scoped(db, svc.Course, organization_id)


@router.get("/courses/{course_id}", response_model=CourseRead)
def get_course(
    course_id: UUID,
    db: Session = Depends(get_db),
    user: User = Depends(manager),
):
    organization_id = svc.require_manage(user)

    course = svc.get_scoped(
        db,
        svc.Course,
        course_id,
        organization_id,
    )

    if course is None:
        raise HTTPException(
            status_code=404,
            detail="Course not found",
        )

    return course


@router.post(
    "/courses",
    response_model=CourseRead,
    status_code=201,
)
def create_course(
    payload: CourseCreate,
    db: Session = Depends(get_db),
    user: User = Depends(manager),
):
    organization_id = svc.require_manage(user)

    return svc.create_course(
        db,
        payload,
        organization_id,
    )


@router.patch(
    "/courses/{course_id}",
    response_model=CourseRead,
)
def update_course(
    course_id: UUID,
    payload: CourseUpdate,
    db: Session = Depends(get_db),
    user: User = Depends(manager),
):
    organization_id = svc.require_manage(user)

    return svc.update_course(
        db,
        course_id,
        payload,
        organization_id,
    )


@router.delete(
    "/courses/{course_id}",
    status_code=204,
)
def delete_course(
    course_id: UUID,
    db: Session = Depends(get_db),
    user: User = Depends(manager),
):
    organization_id = svc.require_manage(user)

    svc.delete_course(
        db,
        course_id,
        organization_id,
    )

    return None


# ============================================================
# COURSE OFFERINGS
# ============================================================

@router.get(
    "/course-offerings",
    response_model=list[OfferingRead],
)
def list_course_offerings(
    db: Session = Depends(get_db),
    user: User = Depends(manager),
):
    organization_id = svc.require_manage(user)

    return svc.list_scoped(
        db,
        svc.CourseOffering,
        organization_id,
    )


@router.get(
    "/course-offerings/{offering_id}",
    response_model=OfferingRead,
)
def get_course_offering(
    offering_id: UUID,
    db: Session = Depends(get_db),
    user: User = Depends(manager),
):
    organization_id = svc.require_manage(user)

    offering = svc.get_scoped(
        db,
        svc.CourseOffering,
        offering_id,
        organization_id,
    )

    if offering is None:
        raise HTTPException(
            status_code=404,
            detail="Course offering not found",
        )

    return offering


@router.post(
    "/course-offerings",
    response_model=OfferingRead,
    status_code=201,
)
def create_course_offering(
    payload: OfferingCreate,
    db: Session = Depends(get_db),
    user: User = Depends(manager),
):
    organization_id = svc.require_manage(user)

    return svc.create_offering(
        db,
        payload,
        organization_id,
    )


@router.patch(
    "/course-offerings/{offering_id}",
    response_model=OfferingRead,
)
def update_course_offering(
    offering_id: UUID,
    payload: OfferingUpdate,
    db: Session = Depends(get_db),
    user: User = Depends(manager),
):
    organization_id = svc.require_manage(user)

    return svc.update_offering(
        db,
        offering_id,
        payload,
        organization_id,
    )


# ============================================================
# STUDENTS
# ============================================================

@router.get(
    "/students",
    response_model=list[StudentRead],
)
def list_students(
    db: Session = Depends(get_db),
    user: User = Depends(manager),
):
    organization_id = svc.require_manage(user)

    return svc.list_students(
        db,
        organization_id,
    )


# ============================================================
# TEACHERS
# ============================================================

@router.get(
    "/teachers",
    response_model=list[TeacherRead],
)
def list_teachers(
    db: Session = Depends(get_db),
    user: User = Depends(manager),
):
    organization_id = svc.require_manage(user)

    return svc.list_teachers(
        db,
        organization_id,
    )


# ============================================================
# ENROLLMENTS
# ============================================================

@router.get(
    "/enrollments",
    response_model=list[EnrollmentRead],
)
def list_enrollments(
    db: Session = Depends(get_db),
    user: User = Depends(manager),
):
    organization_id = svc.require_manage(user)

    return svc.list_enrollments(
        db,
        organization_id,
    )


@router.get(
    "/enrollments/{enrollment_id}",
    response_model=EnrollmentRead,
)
def get_enrollment(
    enrollment_id: UUID,
    db: Session = Depends(get_db),
    user: User = Depends(manager),
):
    organization_id = svc.require_manage(user)

    enrollment = svc.get_scoped(
        db,
        svc.Enrollment,
        enrollment_id,
        organization_id,
    )

    if enrollment is None:
        raise HTTPException(
            status_code=404,
            detail="Enrollment not found",
        )

    return enrollment


@router.post(
    "/enrollments",
    response_model=EnrollmentRead,
    status_code=201,
)
def create_enrollment(
    payload: EnrollmentCreate,
    db: Session = Depends(get_db),
    user: User = Depends(manager),
):
    organization_id = svc.require_manage(user)

    return svc.create_enrollment(
        db,
        payload,
        organization_id,
        user,
    )


@router.patch(
    "/enrollments/{enrollment_id}",
    response_model=EnrollmentRead,
)
def update_enrollment(
    enrollment_id: UUID,
    payload: EnrollmentStatusUpdate,
    db: Session = Depends(get_db),
    user: User = Depends(manager),
):
    organization_id = svc.require_manage(user)

    return svc.update_enrollment_status(
        db,
        enrollment_id,
        payload,
        organization_id,
    )