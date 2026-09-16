from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.organization import Organization, OrganizationStatus
from app.models.user import User, UserStatus
from app.schemas.auth import LoginRequest, TokenResponse, UserResponse
from app.security.dependencies import get_current_user
from app.security.jwt import create_access_token
from app.security.password import verify_password

router = APIRouter(prefix="/auth", tags=["authentication"])


@router.post("/login", response_model=TokenResponse)
def login(payload: LoginRequest, db: Session = Depends(get_db)) -> TokenResponse:
    user = db.scalar(select(User).where(User.email == str(payload.email).lower()))

    # Keep credential failures generic to reduce account enumeration.
    if user is None or not verify_password(payload.password, user.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid email or password")

    if user.status != UserStatus.ACTIVE:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Account is not active")

    if user.organization_id is not None:
        organization = db.get(Organization, user.organization_id)
        if organization is None or organization.status not in {OrganizationStatus.ACTIVE, OrganizationStatus.TRIAL}:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Organization access is currently unavailable")

    return TokenResponse(access_token=create_access_token(user.id))


@router.get("/me", response_model=UserResponse)
def me(current_user: User = Depends(get_current_user)) -> UserResponse:
    return UserResponse(
        id=current_user.id,
        email=current_user.email,
        full_name=current_user.full_name,
        role=current_user.role,
        organization_id=current_user.organization_id,
        is_active=current_user.status == UserStatus.ACTIVE,
    )
