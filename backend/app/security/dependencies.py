from collections.abc import Callable, Generator
from uuid import UUID

from fastapi import Depends, HTTPException, status
from fastapi.concurrency import run_in_threadpool
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


async def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    db: Session = Depends(get_db),
) -> Generator[User, None, None]:
    """
    Authenticate the current user and bind the user's organization
    to the request tenant context.

    The dependency itself is async so the ContextVar is established
    in the request execution context before synchronous endpoints and
    services are dispatched to the threadpool.
    """

    if credentials is None or credentials.scheme.lower() != "bearer":
        raise authentication_error()

    try:
        payload = decode_access_token(credentials.credentials)
        user_id = UUID(payload["sub"])

        if payload.get("type") != "access":
            raise ValueError("Invalid token type")

    except Exception:
        raise authentication_error() from None

    # SQLAlchemy Session is synchronous, so database operations are
    # explicitly moved to the threadpool.
    user = await run_in_threadpool(
        lambda: db.scalar(
            select(User).where(User.id == user_id)
        )
    )

    if user is None or user.status != UserStatus.ACTIVE:
        raise authentication_error()

    if user.organization_id is not None:

        organization = await run_in_threadpool(
            lambda: db.get(
                Organization,
                user.organization_id,
            )
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

        # IMPORTANT:
        # This now executes in the async request context rather than
        # inside the worker thread performing the database lookup.
        set_current_organization(user.organization_id)

    try:
        yield user

    finally:
        if user.organization_id is not None:
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