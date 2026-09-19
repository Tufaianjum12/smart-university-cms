from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.user import User, UserRole
from app.models import Course, CourseOffering, Student, Teacher
from app.schemas.academic import StudentRead, TeacherRead
from app.security.dependencies import get_current_user, require_roles
from app.schemas.course import *
from app.services import course_service as svc


router = APIRouter(tags=["Phase 5 Courses & Enrollment"])


admin = Depends(
    require_roles(
        UserRole.UNIVERSITY_ADMIN,
        UserRole.DEPARTMENT_ADMIN,
    )
)


@router.post(
    "/courses",
    response_model=CourseRead,
    status_code=201,
)
def create_course(
    p: CourseCreate,
    db: Session = Depends(get_db),
    u: User = admin,
):
    return svc.create_course(db, p)


@router.get(
    "/courses",
    response_model=list[CourseRead],
)
def list_courses(
    db: Session = Depends(get_db),
    u: User = Depends(get_current_user),
):
    return svc.list_scoped(db, Course)


@router.get(
    "/courses/{id}",
    response_model=CourseRead,
)
def get_course(
    id: UUID,
    db: Session = Depends(get_db),
    u: User = Depends(get_current_user),
):
    return svc.get_or_404(
        db,
        Course,
        id,
        "Course",
    )


@router.patch(
    "/courses/{id}",
    response_model=CourseRead,
)
def update_course(
    id: UUID,
    p: CourseUpdate,
    db: Session = Depends(get_db),
    u: User = admin,
):
    return svc.update_course(db, id, p)


@router.delete(
    "/courses/{id}",
    status_code=204,
)
def archive_course(
    id: UUID,
    db: Session = Depends(get_db),
    u: User = admin,
):
    svc.archive_course(db, id)


@router.post(
    "/courses/{id}/prerequisites",
    response_model=PrerequisiteRead,
    status_code=201,
)
def add_prereq(
    id: UUID,
    p: PrerequisiteCreate,
    db: Session = Depends(get_db),
    u: User = admin,
):
    return svc.add_prereq(db, id, p)


@router.get(
    "/courses/{id}/prerequisites",
    response_model=list[PrerequisiteRead],
)
def list_prereq(
    id: UUID,
    db: Session = Depends(get_db),
    u: User = Depends(get_current_user),
):
    return svc.list_prereq(db, id)


@router.delete(
    "/prerequisites/{id}",
    status_code=204,
)
def remove_prereq(
    id: UUID,
    db: Session = Depends(get_db),
    u: User = admin,
):
    svc.remove_prereq(db, id)


@router.post(
    "/programs/{id}/curriculum",
    response_model=CurriculumRead,
    status_code=201,
)
def add_curriculum(
    id: UUID,
    p: CurriculumCreate,
    db: Session = Depends(get_db),
    u: User = admin,
):
    return svc.add_curriculum(db, id, p)


@router.get(
    "/programs/{id}/curriculum",
    response_model=list[CurriculumRead],
)
def list_curriculum(
    id: UUID,
    db: Session = Depends(get_db),
    u: User = Depends(get_current_user),
):
    return svc.list_curriculum(db, id)


@router.patch(
    "/curriculum/{id}",
    response_model=CurriculumRead,
)
def update_curriculum(
    id: UUID,
    p: CurriculumUpdate,
    db: Session = Depends(get_db),
    u: User = admin,
):
    return svc.update_curriculum(db, id, p)


@router.delete(
    "/curriculum/{id}",
    status_code=204,
)
def remove_curriculum(
    id: UUID,
    db: Session = Depends(get_db),
    u: User = admin,
):
    svc.remove_curriculum(db, id)


@router.post(
    "/course-offerings",
    response_model=OfferingRead,
    status_code=201,
)
def create_offering(
    p: OfferingCreate,
    db: Session = Depends(get_db),
    u: User = admin,
):
    return svc.create_offering(db, p)


@router.get(
    "/course-offerings",
    response_model=list[OfferingRead],
)
def list_offerings(
    db: Session = Depends(get_db),
    u: User = Depends(get_current_user),
):
    return svc.list_offerings_for_user(db, u)


@router.get(
    "/course-offerings/{id}",
    response_model=OfferingRead,
)
def get_offering(
    id: UUID,
    db: Session = Depends(get_db),
    u: User = Depends(get_current_user),
):
    return svc.get_or_404(
        db,
        CourseOffering,
        id,
        "Course offering",
    )


@router.patch(
    "/course-offerings/{id}",
    response_model=OfferingRead,
)
def update_offering(
    id: UUID,
    p: OfferingUpdate,
    db: Session = Depends(get_db),
    u: User = admin,
):
    return svc.update_offering(db, id, p)


@router.delete(
    "/course-offerings/{id}",
    status_code=204,
)
def archive_offering(
    id: UUID,
    db: Session = Depends(get_db),
    u: User = admin,
):
    svc.archive_offering(db, id)


@router.get(
    "/students",
    response_model=list[StudentRead],
)
def list_students(
    db: Session = Depends(get_db),
    u: User = Depends(
        require_roles(
            UserRole.UNIVERSITY_ADMIN,
            UserRole.DEPARTMENT_ADMIN,
        )
    ),
):
    return svc.list_scoped(db, Student)


@router.get(
    "/teachers",
    response_model=list[TeacherRead],
)
def list_teachers(
    db: Session = Depends(get_db),
    u: User = Depends(
        require_roles(
            UserRole.UNIVERSITY_ADMIN,
            UserRole.DEPARTMENT_ADMIN,
        )
    ),
):
    return svc.list_scoped(db, Teacher)


@router.post(
    "/enrollments",
    response_model=EnrollmentRead,
    status_code=201,
)
def enroll(
    p: EnrollmentCreate,
    db: Session = Depends(get_db),
    u: User = Depends(get_current_user),
):
    if u.role not in {
        UserRole.UNIVERSITY_ADMIN,
        UserRole.DEPARTMENT_ADMIN,
        UserRole.STUDENT,
    }:
        raise HTTPException(
            status_code=403,
            detail="Enrollment permission required",
        )

    return svc.create_enrollment(
        db,
        p,
        u,
        admin=u.role
        in {
            UserRole.UNIVERSITY_ADMIN,
            UserRole.DEPARTMENT_ADMIN,
        },
    )


@router.get(
    "/enrollments",
    response_model=list[EnrollmentRead],
)
def list_enrollments(
    student_id: UUID | None = None,
    course_offering_id: UUID | None = None,
    db: Session = Depends(get_db),
    u: User = Depends(get_current_user),
):
    if u.role == UserRole.STUDENT:
        student = svc._student_for_user(db, u)

        if student is None:
            return []

        student_id = student.id

    return svc.list_enrollments(
        db,
        student_id,
        course_offering_id,
    )


@router.get(
    "/enrollments/{id}",
    response_model=EnrollmentRead,
)
def get_enrollment(
    id: UUID,
    db: Session = Depends(get_db),
    u: User = Depends(get_current_user),
):
    x = svc.get_enrollment(db, id)

    if u.role == UserRole.STUDENT:
        s = svc._student_for_user(db, u)

        if s is None or x.student_id != s.id:
            raise HTTPException(
                status_code=403,
                detail="You may only view your own enrollments",
            )

    return x


@router.patch(
    "/enrollments/{id}",
    response_model=EnrollmentRead,
)
def update_enrollment(
    id: UUID,
    p: EnrollmentStatusUpdate,
    db: Session = Depends(get_db),
    u: User = admin,
):
    return svc.update_enrollment(
        db,
        id,
        p,
    )