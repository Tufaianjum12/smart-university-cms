from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.academic import Student
from app.models.user import User, UserRole
from app.security.dependencies import get_current_user, require_super_admin

router = APIRouter(prefix="/security", tags=["authorization"])


@router.get("/tenant-test")
def tenant_test(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Small Phase-3 proof endpoint. Tenant users only see students from their server-derived tenant."""
    if current_user.organization_id is None:
        return {"organization_id": None, "records": []}
    rows = db.scalars(
        select(Student).where(Student.organization_id == current_user.organization_id)
    ).all()
    return {
        "organization_id": str(current_user.organization_id),
        "records": [str(row.id) for row in rows],
    }


@router.get("/super-admin-test")
def super_admin_test(current_user: User = Depends(require_super_admin)):
    return {"message": "Super Admin authorization accepted", "role": current_user.role.value}
