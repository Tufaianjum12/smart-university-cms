from datetime import datetime
from uuid import UUID
from pydantic import BaseModel, ConfigDict, Field
from app.models.organization import OrganizationStatus, OrganizationType


class OrganizationCreate(BaseModel):
    name: str = Field(min_length=2, max_length=200)
    slug: str = Field(min_length=2, max_length=120, pattern=r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
    organization_type: OrganizationType
    timezone: str = "UTC"
    locale: str = "en-US"

class OrganizationRead(OrganizationCreate):
    id: UUID
    status: OrganizationStatus
    created_at: datetime
    updated_at: datetime
    model_config = ConfigDict(from_attributes=True)
