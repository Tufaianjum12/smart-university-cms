from __future__ import annotations
from datetime import date
from uuid import UUID
from sqlalchemy import select, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from app.db.tenant import get_current_organization_id
from app.models import (Organization, OrganizationSettings, Campus, Department, Program, AcademicSession, Semester, Section, Classroom)
from app.models.user import User, UserRole

MANAGE_ROLES = {UserRole.UNIVERSITY_ADMIN}


def org_id() -> UUID:
    return get_current_organization_id()


def ensure_org_user(user: User) -> UUID:
    if user.organization_id is None:
        raise HTTPException(status_code=403, detail="Organization membership required")
    return user.organization_id


def require_manage(user: User) -> UUID:
    if user.role not in MANAGE_ROLES:
        raise HTTPException(status_code=403, detail="Organization administration permission required")
    return ensure_org_user(user)


def not_found(name: str):
    raise HTTPException(status_code=404, detail=f"{name} not found")


def commit(db: Session):
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(status_code=409, detail="Operation violates a database constraint") from exc


def scoped(db, model, object_id: UUID | None = None):
    stmt = select(model).where(model.organization_id == org_id())
    if object_id is not None:
        stmt = stmt.where(model.id == object_id)
    return db.scalar(stmt)


def scoped_list(db, model):
    return list(db.scalars(select(model).where(model.organization_id == org_id()).order_by(model.created_at.desc())).all())


def get_org(db: Session):
    return db.scalar(select(Organization).where(Organization.id == org_id()))


def get_settings(db: Session):
    settings = db.scalar(select(OrganizationSettings).where(OrganizationSettings.organization_id == org_id()))
    if settings is None:
        settings = OrganizationSettings(organization_id=org_id())
        db.add(settings); db.flush()
    return settings


def validate_relation(db: Session, model, object_id: UUID, label: str):
    obj = scoped(db, model, object_id)
    if obj is None:
        not_found(label)
    return obj


def create_campus(db, payload):
    item = Campus(organization_id=org_id(), **payload.model_dump())
    db.add(item); commit(db); db.refresh(item); return item

def update_campus(db, item_id, payload):
    item = validate_relation(db, Campus, item_id, "Campus")
    for k,v in payload.model_dump(exclude_unset=True).items(): setattr(item,k,v)
    commit(db); db.refresh(item); return item

def delete_campus(db, item_id):
    item = validate_relation(db, Campus, item_id, "Campus"); item.is_active=False; commit(db)

def create_department(db, payload):
    validate_relation(db, Campus, payload.campus_id, "Campus")
    item=Department(organization_id=org_id(), **payload.model_dump()); db.add(item); commit(db); db.refresh(item); return item

def update_department(db,item_id,payload):
    item=validate_relation(db,Department,item_id,"Department"); data=payload.model_dump(exclude_unset=True)
    if "campus_id" in data: validate_relation(db,Campus,data["campus_id"],"Campus")
    for k,v in data.items(): setattr(item,k,v)
    commit(db); db.refresh(item); return item

def delete_department(db,item_id):
    item=validate_relation(db,Department,item_id,"Department"); item.is_active=False; commit(db)

def create_program(db,payload):
    validate_relation(db,Department,payload.department_id,"Department")
    item=Program(organization_id=org_id(),**payload.model_dump()); db.add(item); commit(db); db.refresh(item); return item

def update_program(db,item_id,payload):
    item=validate_relation(db,Program,item_id,"Program"); data=payload.model_dump(exclude_unset=True)
    if "department_id" in data: validate_relation(db,Department,data["department_id"],"Department")
    for k,v in data.items(): setattr(item,k,v)
    commit(db); db.refresh(item); return item

def delete_program(db,item_id):
    item=validate_relation(db,Program,item_id,"Program"); item.is_active=False; commit(db)

def create_session(db,payload):
    data=payload.model_dump()
    if data.get("is_current"):
        db.execute(update(AcademicSession).where(AcademicSession.organization_id==org_id()).values(is_current=False))
    item=AcademicSession(organization_id=org_id(),**data); db.add(item); commit(db); db.refresh(item); return item

def update_session(db,item_id,payload):
    item=validate_relation(db,AcademicSession,item_id,"Academic session"); data=payload.model_dump(exclude_unset=True)
    if data.get("is_current"):
        db.execute(update(AcademicSession).where(AcademicSession.organization_id==org_id()).values(is_current=False))
    for k,v in data.items(): setattr(item,k,v)
    commit(db); db.refresh(item); return item

def delete_session(db,item_id):
    item=validate_relation(db,AcademicSession,item_id,"Academic session"); item.is_active=False; item.is_current=False; commit(db)

def create_semester(db,payload):
    validate_relation(db,AcademicSession,payload.academic_session_id,"Academic session")
    item=Semester(organization_id=org_id(),**payload.model_dump()); db.add(item); commit(db); db.refresh(item); return item

def update_semester(db,item_id,payload):
    item=validate_relation(db,Semester,item_id,"Semester"); data=payload.model_dump(exclude_unset=True)
    if "academic_session_id" in data: validate_relation(db,AcademicSession,data["academic_session_id"],"Academic session")
    for k,v in data.items(): setattr(item,k,v)
    commit(db); db.refresh(item); return item

def delete_semester(db,item_id):
    item=validate_relation(db,Semester,item_id,"Semester"); item.is_active=False; commit(db)

def create_section(db,payload):
    data=payload.model_dump(); validate_relation(db,Program,data["program_id"],"Program"); validate_relation(db,Semester,data["semester_id"],"Semester")
    if data.get("course_id") is not None:
        from app.models import Course
        validate_relation(db,Course,data["course_id"],"Course")
    item=Section(organization_id=org_id(),**data); db.add(item); commit(db); db.refresh(item); return item

def update_section(db,item_id,payload):
    item=validate_relation(db,Section,item_id,"Section"); data=payload.model_dump(exclude_unset=True)
    if "program_id" in data and data["program_id"]: validate_relation(db,Program,data["program_id"],"Program")
    if "semester_id" in data: validate_relation(db,Semester,data["semester_id"],"Semester")
    if "course_id" in data and data["course_id"]:
        from app.models import Course
        validate_relation(db,Course,data["course_id"],"Course")
    for k,v in data.items(): setattr(item,k,v)
    commit(db); db.refresh(item); return item

def delete_section(db,item_id):
    item=validate_relation(db,Section,item_id,"Section"); item.is_active=False; commit(db)

def create_classroom(db,payload):
    validate_relation(db,Campus,payload.campus_id,"Campus")
    item=Classroom(organization_id=org_id(),**payload.model_dump()); db.add(item); commit(db); db.refresh(item); return item

def update_classroom(db,item_id,payload):
    item=validate_relation(db,Classroom,item_id,"Classroom"); data=payload.model_dump(exclude_unset=True)
    if "campus_id" in data: validate_relation(db,Campus,data["campus_id"],"Campus")
    for k,v in data.items(): setattr(item,k,v)
    commit(db); db.refresh(item); return item

def delete_classroom(db,item_id):
    item=validate_relation(db,Classroom,item_id,"Classroom"); item.is_active=False; commit(db)
