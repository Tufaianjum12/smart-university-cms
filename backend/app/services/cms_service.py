from __future__ import annotations

from uuid import UUID

from fastapi import HTTPException
from sqlalchemy import select, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models import (
    Organization,
    OrganizationSettings,
    Campus,
    Department,
    Program,
    AcademicSession,
    Semester,
    Section,
    Classroom,
)
from app.models.user import User, UserRole


MANAGE_ROLES = {UserRole.UNIVERSITY_ADMIN}


def ensure_org_user(user: User) -> UUID:
    """
    Make sure the authenticated user belongs to an organization.
    The organization_id comes from the authenticated user, not the client.
    """
    if user.organization_id is None:
        raise HTTPException(
            status_code=403,
            detail="Organization membership required",
        )

    return user.organization_id


def require_manage(user: User) -> UUID:
    """
    Check whether the user can manage organization-level CMS data.
    Returns the authenticated user's organization ID.
    """
    if user.role not in MANAGE_ROLES:
        raise HTTPException(
            status_code=403,
            detail="Organization administration permission required",
        )

    return ensure_org_user(user)


def not_found(name: str):
    raise HTTPException(
        status_code=404,
        detail=f"{name} not found",
    )


def commit(db: Session):
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(
            status_code=409,
            detail="Operation violates a database constraint",
        ) from exc


# ============================================================
# TENANT-SCOPED HELPERS
# ============================================================

def scoped(
    db: Session,
    model,
    object_id: UUID | None = None,
    organization_id: UUID | None = None,
):
    """
    Get an object belonging ONLY to the authenticated user's organization.
    """

    if organization_id is None:
        raise HTTPException(
            status_code=403,
            detail="Organization context required",
        )

    stmt = select(model).where(
        model.organization_id == organization_id
    )

    if object_id is not None:
        stmt = stmt.where(model.id == object_id)

    return db.scalar(stmt)


def scoped_list(
    db: Session,
    model,
    organization_id: UUID,
):
    """
    List ONLY records belonging to the authenticated user's organization.
    """

    return list(
        db.scalars(
            select(model)
            .where(model.organization_id == organization_id)
            .order_by(model.created_at.desc())
        ).all()
    )


def get_org(
    db: Session,
    organization_id: UUID,
):
    return db.scalar(
        select(Organization).where(
            Organization.id == organization_id
        )
    )


def get_settings(
    db: Session,
    organization_id: UUID,
):
    settings = db.scalar(
        select(OrganizationSettings).where(
            OrganizationSettings.organization_id == organization_id
        )
    )

    if settings is None:
        settings = OrganizationSettings(
            organization_id=organization_id
        )
        db.add(settings)
        db.flush()

    return settings


def validate_relation(
    db: Session,
    model,
    object_id: UUID,
    label: str,
    organization_id: UUID,
):
    """
    Validate that a related object belongs to the same tenant.
    """

    obj = scoped(
        db,
        model,
        object_id,
        organization_id,
    )

    if obj is None:
        not_found(label)

    return obj


# ============================================================
# CAMPUS
# ============================================================

def create_campus(
    db: Session,
    payload,
    organization_id: UUID,
):
    item = Campus(
        organization_id=organization_id,
        **payload.model_dump(),
    )

    db.add(item)
    commit(db)
    db.refresh(item)

    return item


def update_campus(
    db: Session,
    item_id,
    payload,
    organization_id: UUID,
):
    item = validate_relation(
        db,
        Campus,
        item_id,
        "Campus",
        organization_id,
    )

    for key, value in payload.model_dump(
        exclude_unset=True
    ).items():
        setattr(item, key, value)

    commit(db)
    db.refresh(item)

    return item


def delete_campus(
    db: Session,
    item_id,
    organization_id: UUID,
):
    item = validate_relation(
        db,
        Campus,
        item_id,
        "Campus",
        organization_id,
    )

    item.is_active = False

    commit(db)


# ============================================================
# DEPARTMENT
# ============================================================

def create_department(
    db: Session,
    payload,
    organization_id: UUID,
):
    validate_relation(
        db,
        Campus,
        payload.campus_id,
        "Campus",
        organization_id,
    )

    item = Department(
        organization_id=organization_id,
        **payload.model_dump(),
    )

    db.add(item)
    commit(db)
    db.refresh(item)

    return item


def update_department(
    db: Session,
    item_id,
    payload,
    organization_id: UUID,
):
    item = validate_relation(
        db,
        Department,
        item_id,
        "Department",
        organization_id,
    )

    data = payload.model_dump(
        exclude_unset=True
    )

    if "campus_id" in data:
        validate_relation(
            db,
            Campus,
            data["campus_id"],
            "Campus",
            organization_id,
        )

    for key, value in data.items():
        setattr(item, key, value)

    commit(db)
    db.refresh(item)

    return item


def delete_department(
    db: Session,
    item_id,
    organization_id: UUID,
):
    item = validate_relation(
        db,
        Department,
        item_id,
        "Department",
        organization_id,
    )

    item.is_active = False

    commit(db)


# ============================================================
# PROGRAM
# ============================================================

def create_program(
    db: Session,
    payload,
    organization_id: UUID,
):
    validate_relation(
        db,
        Department,
        payload.department_id,
        "Department",
        organization_id,
    )

    item = Program(
        organization_id=organization_id,
        **payload.model_dump(),
    )

    db.add(item)
    commit(db)
    db.refresh(item)

    return item


def update_program(
    db: Session,
    item_id,
    payload,
    organization_id: UUID,
):
    item = validate_relation(
        db,
        Program,
        item_id,
        "Program",
        organization_id,
    )

    data = payload.model_dump(
        exclude_unset=True
    )

    if "department_id" in data:
        validate_relation(
            db,
            Department,
            data["department_id"],
            "Department",
            organization_id,
        )

    for key, value in data.items():
        setattr(item, key, value)

    commit(db)
    db.refresh(item)

    return item


def delete_program(
    db: Session,
    item_id,
    organization_id: UUID,
):
    item = validate_relation(
        db,
        Program,
        item_id,
        "Program",
        organization_id,
    )

    item.is_active = False

    commit(db)


# ============================================================
# ACADEMIC SESSION
# ============================================================

def create_session(
    db: Session,
    payload,
    organization_id: UUID,
):
    data = payload.model_dump()

    if data.get("is_current"):
        db.execute(
            update(AcademicSession)
            .where(
                AcademicSession.organization_id
                == organization_id
            )
            .values(is_current=False)
        )

    item = AcademicSession(
        organization_id=organization_id,
        **data,
    )

    db.add(item)
    commit(db)
    db.refresh(item)

    return item


def update_session(
    db: Session,
    item_id,
    payload,
    organization_id: UUID,
):
    item = validate_relation(
        db,
        AcademicSession,
        item_id,
        "Academic session",
        organization_id,
    )

    data = payload.model_dump(
        exclude_unset=True
    )

    if data.get("is_current"):
        db.execute(
            update(AcademicSession)
            .where(
                AcademicSession.organization_id
                == organization_id
            )
            .values(is_current=False)
        )

    for key, value in data.items():
        setattr(item, key, value)

    commit(db)
    db.refresh(item)

    return item


def delete_session(
    db: Session,
    item_id,
    organization_id: UUID,
):
    item = validate_relation(
        db,
        AcademicSession,
        item_id,
        "Academic session",
        organization_id,
    )

    item.is_active = False
    item.is_current = False

    commit(db)


# ============================================================
# SEMESTER
# ============================================================

def create_semester(
    db: Session,
    payload,
    organization_id: UUID,
):
    validate_relation(
        db,
        AcademicSession,
        payload.academic_session_id,
        "Academic session",
        organization_id,
    )

    item = Semester(
        organization_id=organization_id,
        **payload.model_dump(),
    )

    db.add(item)
    commit(db)
    db.refresh(item)

    return item


def update_semester(
    db: Session,
    item_id,
    payload,
    organization_id: UUID,
):
    item = validate_relation(
        db,
        Semester,
        item_id,
        "Semester",
        organization_id,
    )

    data = payload.model_dump(
        exclude_unset=True
    )

    if "academic_session_id" in data:
        validate_relation(
            db,
            AcademicSession,
            data["academic_session_id"],
            "Academic session",
            organization_id,
        )

    for key, value in data.items():
        setattr(item, key, value)

    commit(db)
    db.refresh(item)

    return item


def delete_semester(
    db: Session,
    item_id,
    organization_id: UUID,
):
    item = validate_relation(
        db,
        Semester,
        item_id,
        "Semester",
        organization_id,
    )

    item.is_active = False

    commit(db)


# ============================================================
# SECTION
# ============================================================

def create_section(
    db: Session,
    payload,
    organization_id: UUID,
):
    data = payload.model_dump()

    validate_relation(
        db,
        Program,
        data["program_id"],
        "Program",
        organization_id,
    )

    validate_relation(
        db,
        Semester,
        data["semester_id"],
        "Semester",
        organization_id,
    )

    if data.get("course_id") is not None:
        from app.models import Course

        validate_relation(
            db,
            Course,
            data["course_id"],
            "Course",
            organization_id,
        )

    item = Section(
        organization_id=organization_id,
        **data,
    )

    db.add(item)
    commit(db)
    db.refresh(item)

    return item


def update_section(
    db: Session,
    item_id,
    payload,
    organization_id: UUID,
):
    item = validate_relation(
        db,
        Section,
        item_id,
        "Section",
        organization_id,
    )

    data = payload.model_dump(
        exclude_unset=True
    )

    if "program_id" in data and data["program_id"]:
        validate_relation(
            db,
            Program,
            data["program_id"],
            "Program",
            organization_id,
        )

    if "semester_id" in data:
        validate_relation(
            db,
            Semester,
            data["semester_id"],
            "Semester",
            organization_id,
        )

    if "course_id" in data and data["course_id"]:
        from app.models import Course

        validate_relation(
            db,
            Course,
            data["course_id"],
            "Course",
            organization_id,
        )

    for key, value in data.items():
        setattr(item, key, value)

    commit(db)
    db.refresh(item)

    return item


def delete_section(
    db: Session,
    item_id,
    organization_id: UUID,
):
    item = validate_relation(
        db,
        Section,
        item_id,
        "Section",
        organization_id,
    )

    item.is_active = False

    commit(db)


# ============================================================
# CLASSROOM
# ============================================================

def create_classroom(
    db: Session,
    payload,
    organization_id: UUID,
):
    validate_relation(
        db,
        Campus,
        payload.campus_id,
        "Campus",
        organization_id,
    )

    item = Classroom(
        organization_id=organization_id,
        **payload.model_dump(),
    )

    db.add(item)
    commit(db)
    db.refresh(item)

    return item


def update_classroom(
    db: Session,
    item_id,
    payload,
    organization_id: UUID,
):
    item = validate_relation(
        db,
        Classroom,
        item_id,
        "Classroom",
        organization_id,
    )

    data = payload.model_dump(
        exclude_unset=True
    )

    if "campus_id" in data:
        validate_relation(
            db,
            Campus,
            data["campus_id"],
            "Campus",
            organization_id,
        )

    for key, value in data.items():
        setattr(item, key, value)

    commit(db)
    db.refresh(item)

    return item


def delete_classroom(
    db: Session,
    item_id,
    organization_id: UUID,
):
    item = validate_relation(
        db,
        Classroom,
        item_id,
        "Classroom",
        organization_id,
    )

    item.is_active = False

    commit(db)