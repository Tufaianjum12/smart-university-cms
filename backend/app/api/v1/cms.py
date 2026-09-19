from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.models import Organization, OrganizationSettings, Campus, Department, Program, AcademicSession, Semester, Section, Classroom
from app.models.user import User, UserRole
from app.schemas.cms import *
from app.security.dependencies import get_current_user, require_super_admin
from app.services import cms_service as svc

router = APIRouter(tags=["Phase 4 CMS"])

def manager(user: User = Depends(get_current_user)) -> User:
    svc.require_manage(user)
    return user

def tenant_id(user: User) -> UUID:
    return svc.require_manage(user)

# ---------- platform organization management ----------
@router.post("/organizations", response_model=OrganizationAdminRead, status_code=201)
def create_organization(payload: OrganizationCreate, db: Session=Depends(get_db), _:User=Depends(require_super_admin)):
    existing=db.scalar(__import__('sqlalchemy').select(Organization).where(Organization.slug==payload.slug))
    if existing: raise HTTPException(409,"Organization slug already exists")
    org=Organization(**payload.model_dump())
    db.add(org); db.flush(); db.add(OrganizationSettings(organization_id=org.id)); svc.commit(db); db.refresh(org); return org

@router.get("/organizations", response_model=list[OrganizationAdminRead])
def list_organizations(db:Session=Depends(get_db), _:User=Depends(require_super_admin)):
    return list(db.scalars(__import__('sqlalchemy').select(Organization).order_by(Organization.created_at.desc())).all())

@router.get("/organizations/{organization_id}", response_model=OrganizationAdminRead)
def get_organization(organization_id:UUID,db:Session=Depends(get_db),_:User=Depends(require_super_admin)):
    org=db.get(Organization,organization_id)
    if not org: svc.not_found("Organization")
    return org

@router.patch("/organizations/{organization_id}", response_model=OrganizationAdminRead)
def update_organization(organization_id:UUID,payload:OrganizationUpdate,db:Session=Depends(get_db),_:User=Depends(require_super_admin)):
    org=db.get(Organization,organization_id)
    if not org: svc.not_found("Organization")
    for k,v in payload.model_dump(exclude_unset=True).items(): setattr(org,k,v)
    svc.commit(db); db.refresh(org); return org

def set_org_status(organization_id, value, db):
    org=db.get(Organization,organization_id)
    if not org: svc.not_found("Organization")
    org.status=value; svc.commit(db); db.refresh(org); return org

@router.post("/organizations/{organization_id}/activate", response_model=OrganizationAdminRead)
def activate_org(organization_id:UUID,db:Session=Depends(get_db),_:User=Depends(require_super_admin)):
    from app.models.organization import OrganizationStatus
    return set_org_status(organization_id,OrganizationStatus.ACTIVE,db)
@router.post("/organizations/{organization_id}/suspend", response_model=OrganizationAdminRead)
def suspend_org(organization_id:UUID,db:Session=Depends(get_db),_:User=Depends(require_super_admin)):
    from app.models.organization import OrganizationStatus
    return set_org_status(organization_id,OrganizationStatus.SUSPENDED,db)

# ---------- tenant organization ----------
@router.get("/organization", response_model=OrganizationAdminRead)
def my_organization(db:Session=Depends(get_db),user:User=Depends(manager)):
    org=svc.get_org(db)
    if not org: svc.not_found("Organization")
    return org

@router.patch("/organization", response_model=OrganizationAdminRead)
def update_my_organization(payload:OrganizationUpdate,db:Session=Depends(get_db),user:User=Depends(manager)):
    org=svc.get_org(db)
    if not org: svc.not_found("Organization")
    for k,v in payload.model_dump(exclude_unset=True).items(): setattr(org,k,v)
    svc.commit(db); db.refresh(org); return org

@router.get("/organization/settings",response_model=SettingsRead)
def read_settings(db:Session=Depends(get_db),user:User=Depends(manager)): return svc.get_settings(db)
@router.put("/organization/settings",response_model=SettingsRead)
def update_settings(payload:SettingsUpdate,db:Session=Depends(get_db),user:User=Depends(manager)):
    item=svc.get_settings(db)
    for k,v in payload.model_dump().items(): setattr(item,k,v)
    svc.commit(db); db.refresh(item); return item

# ---------- generic tenant CRUD ----------
def crud_routes(prefix, model, create_schema, update_schema, read_schema, create_fn, update_fn, delete_fn, label):
    r=APIRouter(prefix=f"/{prefix}",tags=[label])
    @r.get("",response_model=list[read_schema])
    def listing(db:Session=Depends(get_db),user:User=Depends(manager)): return svc.scoped_list(db,model)
    @r.get("/{item_id}",response_model=read_schema)
    def getting(item_id:UUID,db:Session=Depends(get_db),user:User=Depends(manager)):
        item=svc.scoped(db,model,item_id)
        if item is None: svc.not_found(label)
        return item
    @r.post("",response_model=read_schema,status_code=201)
    def creating(payload:create_schema,db:Session=Depends(get_db),user:User=Depends(manager)): return create_fn(db,payload)
    @r.patch("/{item_id}",response_model=read_schema)
    def updating(item_id:UUID,payload:update_schema,db:Session=Depends(get_db),user:User=Depends(manager)): return update_fn(db,item_id,payload)
    @r.delete("/{item_id}",status_code=204)
    def deleting(item_id:UUID,db:Session=Depends(get_db),user:User=Depends(manager)):
        delete_fn(db,item_id); return None
    return r

router.include_router(crud_routes("campuses",Campus,CampusCreate,CampusUpdate,CampusRead,svc.create_campus,svc.update_campus,svc.delete_campus,"Campus"))
router.include_router(crud_routes("departments",Department,DepartmentCreate,DepartmentUpdate,DepartmentRead,svc.create_department,svc.update_department,svc.delete_department,"Department"))
router.include_router(crud_routes("programs",Program,ProgramCreate,ProgramUpdate,ProgramRead,svc.create_program,svc.update_program,svc.delete_program,"Program"))
router.include_router(crud_routes("academic-sessions",AcademicSession,SessionCreate,SessionUpdate,SessionRead,svc.create_session,svc.update_session,svc.delete_session,"Academic session"))
router.include_router(crud_routes("semesters",Semester,SemesterCreate,SemesterUpdate,SemesterRead,svc.create_semester,svc.update_semester,svc.delete_semester,"Semester"))
router.include_router(crud_routes("sections",Section,SectionCreate,SectionUpdate,SectionRead,svc.create_section,svc.update_section,svc.delete_section,"Section"))
router.include_router(crud_routes("classrooms",Classroom,ClassroomCreate,ClassroomUpdate,ClassroomRead,svc.create_classroom,svc.update_classroom,svc.delete_classroom,"Classroom"))
