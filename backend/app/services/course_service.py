from __future__ import annotations
from datetime import datetime, timezone
from uuid import UUID
from fastapi import HTTPException
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from app.db.tenant import get_current_organization_id
from app.models import (Course, CoursePrerequisite, ProgramCourse, CourseOffering, Enrollment, Department, Program, Semester, AcademicSession, Section, Teacher, Student, EnrollmentStatus)
from app.models.academic import CourseType

MANAGE_ROLES = {"university_admin"}

def oid():
    value = get_current_organization_id()
    if value is None: raise HTTPException(403, "Organization membership required")
    return value

def fail(name): raise HTTPException(404, f"{name} not found")
def scoped(db, model, ident):
    return db.scalar(select(model).where(model.organization_id==oid(), model.id==ident))
def list_scoped(db, model):
    return list(db.scalars(select(model).where(model.organization_id==oid()).order_by(model.created_at.desc())).all())
def get_or_404(db, model, ident, name):
    obj=scoped(db,model,ident)
    if obj is None: fail(name)
    return obj

def commit(db):
    try: db.commit()
    except IntegrityError as e:
        db.rollback(); raise HTTPException(409,"Operation violates a database constraint") from e

def create_course(db,p):
    d=p.model_dump(); get_or_404(db,Department,d['department_id'],'Department')
    x=Course(organization_id=oid(),**d); db.add(x); commit(db); db.refresh(x); return x

def update_course(db,i,p):
    x=get_or_404(db,Course,i,'Course'); d=p.model_dump(exclude_unset=True)
    if 'department_id' in d: get_or_404(db,Department,d['department_id'],'Department')
    for k,v in d.items(): setattr(x,k,v)
    commit(db); db.refresh(x); return x

def archive_course(db,i): x=get_or_404(db,Course,i,'Course'); x.is_active=False; commit(db)

def add_prereq(db,course_id,p):
    course=get_or_404(db,Course,course_id,'Course'); pre=get_or_404(db,Course,p.prerequisite_course_id,'Prerequisite course')
    if course.id==pre.id: raise HTTPException(400,'A course cannot be its own prerequisite')
    x=CoursePrerequisite(organization_id=oid(),course_id=course.id,prerequisite_course_id=pre.id); db.add(x); commit(db); db.refresh(x); return x

def list_prereq(db,course_id): get_or_404(db,Course,course_id,'Course'); return list(db.scalars(select(CoursePrerequisite).where(CoursePrerequisite.organization_id==oid(),CoursePrerequisite.course_id==course_id)).all())
def remove_prereq(db,i): x=get_or_404(db,CoursePrerequisite,i,'Prerequisite'); db.delete(x); commit(db)

def add_curriculum(db,program_id,p):
    program=get_or_404(db,Program,program_id,'Program'); course=get_or_404(db,Course,p.course_id,'Course')
    if p.recommended_semester_id: get_or_404(db,Semester,p.recommended_semester_id,'Semester')
    x=ProgramCourse(organization_id=oid(),program_id=program.id,**p.model_dump()); db.add(x); commit(db); db.refresh(x); return x

def list_curriculum(db,program_id): get_or_404(db,Program,program_id,'Program'); return list(db.scalars(select(ProgramCourse).where(ProgramCourse.organization_id==oid(),ProgramCourse.program_id==program_id).order_by(ProgramCourse.sort_order,ProgramCourse.created_at)).all())
def update_curriculum(db,i,p):
    x=get_or_404(db,ProgramCourse,i,'Curriculum entry'); d=p.model_dump(exclude_unset=True)
    if 'recommended_semester_id' in d and d['recommended_semester_id']: get_or_404(db,Semester,d['recommended_semester_id'],'Semester')
    for k,v in d.items(): setattr(x,k,v)
    commit(db); db.refresh(x); return x
def remove_curriculum(db,i): x=get_or_404(db,ProgramCourse,i,'Curriculum entry'); db.delete(x); commit(db)

def validate_offering_relations(db,d):
    course=get_or_404(db,Course,d['course_id'],'Course'); section=get_or_404(db,Section,d['section_id'],'Section'); sess=get_or_404(db,AcademicSession,d['academic_session_id'],'Academic session'); sem=get_or_404(db,Semester,d['semester_id'],'Semester')
    if sem.academic_session_id != sess.id: raise HTTPException(400,'Semester does not belong to the academic session')
    if section.semester_id != sem.id: raise HTTPException(400,'Section does not belong to the selected semester')
    if section.course_id is not None and section.course_id != course.id:
        raise HTTPException(400, 'Section is already associated with a different legacy course')
    if d.get('teacher_id') is not None: get_or_404(db,Teacher,d['teacher_id'],'Teacher')
    if not course.is_active or not section.is_active or not sess.is_active or not sem.is_active: raise HTTPException(400,'Course, section, session and semester must be active')
    return course,section,sess,sem

def create_offering(db,p):
    d=p.model_dump(); validate_offering_relations(db,d); x=CourseOffering(organization_id=oid(),**d); db.add(x); commit(db); db.refresh(x); return x

def update_offering(db,i,p):
    x=get_or_404(db,CourseOffering,i,'Course offering'); d=p.model_dump(exclude_unset=True); merged={k:getattr(x,k) for k in ['course_id','section_id','academic_session_id','semester_id','teacher_id','max_students']}; merged.update({k:v for k,v in d.items() if k!='is_active'}); validate_offering_relations(db,merged)
    for k,v in d.items(): setattr(x,k,v)
    commit(db); db.refresh(x); return x
def archive_offering(db,i): x=get_or_404(db,CourseOffering,i,'Course offering'); x.is_active=False; commit(db)

def list_offerings_for_user(db, user):
    if user.role.value == "teacher":
        teacher = db.scalar(select(Teacher).where(
            Teacher.organization_id == oid(),
            Teacher.user_id == user.id,
            Teacher.status == "active",
        ))
        if teacher is None:
            return []
        return list(db.scalars(
            select(CourseOffering).where(
                CourseOffering.organization_id == oid(),
                CourseOffering.teacher_id == teacher.id,
                CourseOffering.is_active.is_(True),
            ).order_by(CourseOffering.created_at.desc())
        ).all())
    if user.role.value != "student":
        return list_scoped(db, CourseOffering)
    student=_student_for_user(db,user)
    if student is None: return []
    return list(db.scalars(select(CourseOffering).join(Section, (Section.organization_id==CourseOffering.organization_id) & (Section.id==CourseOffering.section_id)).where(CourseOffering.organization_id==oid(), CourseOffering.is_active.is_(True), Section.program_id==student.program_id, CourseOffering.academic_session_id==student.academic_session_id).order_by(CourseOffering.created_at.desc())).all())

def _student_for_user(db,user):
    return db.scalar(select(Student).where(Student.organization_id==oid(), Student.user_id==user.id))

def create_enrollment(db,p,user,admin=False):
    if not admin:
        student=_student_for_user(db,user)
        if student is None:
            raise HTTPException(403, 'Student profile is required for enrollment')
        sid=student.id
        if p.student_id is not None and p.student_id != sid:
            raise HTTPException(403, 'Students may only enroll themselves')
    else:
        if p.student_id is None:
            raise HTTPException(422, 'student_id is required for administrator enrollment')
        sid=p.student_id
    student=get_or_404(db,Student,sid,'Student')
    offering=db.scalar(select(CourseOffering).where(CourseOffering.organization_id==oid(), CourseOffering.id==p.course_offering_id).with_for_update())
    if offering is None: fail('Course offering')
    if student.status.value != 'active': raise HTTPException(400,'Inactive students cannot enroll')
    if not offering.is_active: raise HTTPException(400,'Course offering is not active')
    section=get_or_404(db,Section,offering.section_id,'Section')
    if student.program_id != section.program_id: raise HTTPException(400,'Student program does not match the course offering section')
    if student.academic_session_id != offering.academic_session_id: raise HTTPException(400,'Student academic session does not match the offering')
    existing=db.scalar(select(Enrollment).where(Enrollment.organization_id==oid(),Enrollment.student_id==sid,Enrollment.course_offering_id==offering.id))
    if existing: raise HTTPException(409,'Student is already enrolled in this course offering')
    if offering.max_students is not None:
        count=db.scalar(select(func.count()).select_from(Enrollment).where(Enrollment.organization_id==oid(),Enrollment.course_offering_id==offering.id,Enrollment.status==EnrollmentStatus.ENROLLED)) or 0
        if count >= offering.max_students: raise HTTPException(409,'Course offering capacity has been reached')
    x=Enrollment(organization_id=oid(),student_id=sid,course_offering_id=offering.id)
    db.add(x); commit(db); db.refresh(x); return x

def list_enrollments(db,student_id=None,offering_id=None):
    stmt=select(Enrollment).where(Enrollment.organization_id==oid())
    if student_id: stmt=stmt.where(Enrollment.student_id==student_id)
    if offering_id: stmt=stmt.where(Enrollment.course_offering_id==offering_id)
    return list(db.scalars(stmt.order_by(Enrollment.created_at.desc())).all())

def get_enrollment(db,i): return get_or_404(db,Enrollment,i,'Enrollment')
def update_enrollment(db,i,p):
    x=get_enrollment(db,i); x.status=p.status
    x.dropped_at=datetime.now(timezone.utc) if p.status in {EnrollmentStatus.DROPPED,EnrollmentStatus.WITHDRAWN} else None
    commit(db); db.refresh(x); return x
