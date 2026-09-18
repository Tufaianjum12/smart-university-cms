from datetime import date, datetime
from uuid import UUID
from pydantic import BaseModel, ConfigDict, Field, model_validator
from app.models import OrganizationStatus, OrganizationType

class OrganizationUpdate(BaseModel):
    name: str | None = Field(None,min_length=2,max_length=200)
    organization_type: OrganizationType | None = None
    timezone: str | None = Field(None,max_length=64)
    locale: str | None = Field(None,max_length=16)

class OrganizationAdminRead(BaseModel):
    id: UUID; name: str; slug: str; organization_type: OrganizationType; status: OrganizationStatus; timezone: str; locale: str; created_at: datetime; updated_at: datetime
    model_config=ConfigDict(from_attributes=True)

class OrganizationCreate(BaseModel):
    name:str=Field(min_length=2,max_length=200); slug:str=Field(min_length=2,max_length=120,pattern=r"^[a-z0-9]+(?:-[a-z0-9]+)*$"); organization_type:OrganizationType; timezone:str=Field(default="UTC",max_length=64); locale:str=Field(default="en-US",max_length=16)

class SettingsUpdate(BaseModel):
    minimum_attendance_percentage: float = Field(75, ge=0, le=100)
    grading_scale: dict = Field(default_factory=dict)
    academic_rules: dict = Field(default_factory=dict)

class SettingsRead(SettingsUpdate):
    organization_id: UUID; created_at: datetime; updated_at: datetime
    model_config=ConfigDict(from_attributes=True)

class CampusCreate(BaseModel):
    name:str=Field(min_length=2,max_length=160); code:str=Field(min_length=1,max_length=40); address:str|None=Field(None,max_length=2000)
class CampusUpdate(BaseModel):
    name:str|None=Field(None,min_length=2,max_length=160); code:str|None=Field(None,min_length=1,max_length=40); address:str|None=None; is_active:bool|None=None
class CampusRead(CampusCreate):
    id:UUID; organization_id:UUID; is_active:bool; created_at:datetime; updated_at:datetime; model_config=ConfigDict(from_attributes=True)

class DepartmentCreate(BaseModel):
    campus_id:UUID; name:str=Field(min_length=2,max_length=160); code:str=Field(min_length=1,max_length=40)
class DepartmentUpdate(BaseModel):
    campus_id:UUID|None=None; name:str|None=Field(None,min_length=2,max_length=160); code:str|None=Field(None,min_length=1,max_length=40); is_active:bool|None=None
class DepartmentRead(DepartmentCreate):
    id:UUID; organization_id:UUID; is_active:bool; created_at:datetime; updated_at:datetime; model_config=ConfigDict(from_attributes=True)

class ProgramCreate(BaseModel):
    department_id:UUID; name:str=Field(min_length=2,max_length=160); code:str=Field(min_length=1,max_length=40); duration_years:int|None=Field(None,ge=1,le=10)
class ProgramUpdate(BaseModel):
    department_id:UUID|None=None; name:str|None=Field(None,min_length=2,max_length=160); code:str|None=Field(None,min_length=1,max_length=40); duration_years:int|None=Field(None,ge=1,le=10); is_active:bool|None=None
class ProgramRead(ProgramCreate):
    id:UUID; organization_id:UUID; is_active:bool; created_at:datetime; updated_at:datetime; model_config=ConfigDict(from_attributes=True)

class SessionCreate(BaseModel):
    code:str=Field(min_length=1,max_length=40); name:str=Field(min_length=2,max_length=100); start_date:date|None=None; end_date:date|None=None; is_current:bool=False
    @model_validator(mode="after")
    def dates(self):
        if self.start_date and self.end_date and self.end_date<self.start_date: raise ValueError("end_date must be on or after start_date")
        return self
class SessionUpdate(BaseModel):
    code:str|None=Field(None,min_length=1,max_length=40); name:str|None=Field(None,min_length=2,max_length=100); start_date:date|None=None; end_date:date|None=None; is_active:bool|None=None; is_current:bool|None=None
class SessionRead(SessionCreate):
    id:UUID; organization_id:UUID; is_active:bool; created_at:datetime; updated_at:datetime; model_config=ConfigDict(from_attributes=True)

class SemesterCreate(BaseModel):
    academic_session_id:UUID; code:str=Field(min_length=1,max_length=40); name:str=Field(min_length=2,max_length=100); start_date:date|None=None; end_date:date|None=None
    @model_validator(mode="after")
    def dates(self):
        if self.start_date and self.end_date and self.end_date<self.start_date: raise ValueError("end_date must be on or after start_date")
        return self
class SemesterUpdate(BaseModel):
    academic_session_id:UUID|None=None; code:str|None=Field(None,min_length=1,max_length=40); name:str|None=Field(None,min_length=2,max_length=100); start_date:date|None=None; end_date:date|None=None; is_active:bool|None=None
class SemesterRead(SemesterCreate):
    id:UUID; organization_id:UUID; is_active:bool; created_at:datetime; updated_at:datetime; model_config=ConfigDict(from_attributes=True)

class SectionCreate(BaseModel):
    semester_id:UUID; program_id:UUID; section_code:str=Field(min_length=1,max_length=40); capacity:int|None=Field(None,gt=0); course_id:UUID|None=None
class SectionUpdate(BaseModel):
    semester_id:UUID|None=None; program_id:UUID|None=None; section_code:str|None=Field(None,min_length=1,max_length=40); capacity:int|None=Field(None,gt=0); course_id:UUID|None=None; is_active:bool|None=None
class SectionRead(SectionCreate):
    id:UUID; organization_id:UUID; is_active:bool; created_at:datetime; updated_at:datetime; model_config=ConfigDict(from_attributes=True)

class ClassroomCreate(BaseModel):
    campus_id:UUID; building:str|None=Field(None,max_length=100); room_code:str=Field(min_length=1,max_length=40); capacity:int=Field(gt=0,le=100000)
class ClassroomUpdate(BaseModel):
    campus_id:UUID|None=None; building:str|None=Field(None,max_length=100); room_code:str|None=Field(None,min_length=1,max_length=40); capacity:int|None=Field(None,gt=0,le=100000); is_active:bool|None=None
class ClassroomRead(ClassroomCreate):
    id:UUID; organization_id:UUID; is_active:bool; created_at:datetime; updated_at:datetime; model_config=ConfigDict(from_attributes=True)
