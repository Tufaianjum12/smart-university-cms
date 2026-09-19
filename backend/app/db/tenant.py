from contextvars import ContextVar
from uuid import UUID


class TenantContextError(RuntimeError):
    """Raised when a tenant context is required but not available."""


_current_organization_id: ContextVar[UUID | None] = ContextVar(
    "current_organization_id",
    default=None,
)


def set_current_organization(organization_id: UUID) -> None:
    """
    Bind an organization/tenant to the current request context.
    """
    _current_organization_id.set(organization_id)


def clear_current_organization() -> None:
    """
    Clear the organization/tenant from the current request context.
    """
    _current_organization_id.set(None)


def get_current_organization_id() -> UUID:
    """
    Return the organization/tenant bound to the current request.

    Raises:
        TenantContextError: if no organization is currently bound.
    """
    organization_id = _current_organization_id.get()

    if organization_id is None:
        raise TenantContextError(
            "No organization is bound to the current request context"
        )

    return organization_id