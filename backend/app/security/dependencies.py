from collections.abc import Callable, Generator
from uuid import UUID

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.db.tenant import clear_current_organization, set_current_organization
from app.models.organization import Organization, OrganizationStatus
from app.models.user import User, UserRole, UserStatus
from app.security.jwt import decode_access_token


bearer_scheme = HTTPBearer(auto_error=False)


def authentication_error() -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Authentication required or token is invalid",
        headers={"WWW-Authenticate": "Bearer"},
    )


def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    db: Session = Depends(get_db),
) -> Generator[User, None, None]:

    if credentials is None or credentials.scheme.lower() != "bearer":
        raise authentication_error()

    try:
        payload = decode_access_token(credentials.credentials)

        user_id = UUID(payload["sub"])

        if payload.get("type") != "access":
            raise ValueError("Invalid token type")

    except Exception:
        raise authentication_error() from None

    user = db.scalar(
        select(User).where(User.id == user_id)
    )

    if user is None or user.status != UserStatus.ACTIVE:
        raise authentication_error()

    organization_id = user.organization_id

    if organization_id is not None:

        organization = db.get(
            Organization,
            organization_id,
        )

        if organization is None:
            raise authentication_error()

        if organization.status not in {
            OrganizationStatus.ACTIVE,
            OrganizationStatus.TRIAL,
        }:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Organization access is currently unavailable",
            )

        # Keep tenant information on the SQLAlchemy Session.
        # The same Session is used by the endpoint/service layer.
        db.info["organization_id"] = organization_id

        # Keep the ContextVar as well for code that uses it elsewhere.
        set_current_organization(organization_id)

    try:
        yield user

    finally:
        db.info.pop("organization_id", None)

        if organization_id is not None:
            clear_current_organization()


def require_roles(*roles: UserRole) -> Callable:

    allowed = set(roles)

    def dependency(
        current_user: User = Depends(get_current_user),
    ) -> User:

        if current_user.role not in allowed:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions",
            )

        return current_user

    return dependency


def require_super_admin(
    current_user: User = Depends(get_current_user),
) -> User:

    if current_user.role != UserRole.SUPER_ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
        detail="Super Admin access required",
        )

    return current_user
