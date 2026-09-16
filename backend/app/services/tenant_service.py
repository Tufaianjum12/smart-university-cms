from uuid import UUID
from sqlalchemy import select
from sqlalchemy.orm import Session
from app.db.tenant import get_current_organization_id
from app.models.organization import Organization


def require_current_organization(db: Session) -> Organization:
    """Resolve the organization from backend-controlled tenant context, never request input."""
    organization_id = get_current_organization_id()
    organization = db.scalar(select(Organization).where(Organization.id == organization_id))
    if organization is None:
        raise LookupError("Current organization does not exist")
    return organization


def assert_same_tenant(*organization_ids: UUID | None) -> None:
    values = [value for value in organization_ids if value is not None]
    if not values or len(set(values)) != 1:
        raise ValueError("Cross-tenant relationship rejected")
    if values[0] != get_current_organization_id():
        raise PermissionError("Object belongs to a different organization")
