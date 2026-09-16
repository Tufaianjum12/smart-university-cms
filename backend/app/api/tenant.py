from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.db.tenant import get_current_organization_id

router = APIRouter(prefix="/tenant", tags=["tenant"])


@router.get("/context")
def tenant_context(db: Session = Depends(get_db)):
    """Phase-2 test endpoint; Phase 3 will bind this context from the authenticated user."""
    return {"organization_id": str(get_current_organization_id())}
