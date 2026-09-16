from contextvars import ContextVar
from uuid import UUID


_current_organization_id: ContextVar[UUID | None] = ContextVar("current_organization_id", default=None)


class TenantContextError(RuntimeError):
    """Raised when tenant-scoped data is accessed without a tenant context."""


def set_current_organization(organization_id: UUID) -> None:
    _current_organization_id.set(organization_id)


def get_current_organization_id() -> UUID:
    organization_id = _current_organization_id.get()
    if organization_id is None:
        raise TenantContextError("No organization is bound to the current request context")
    return organization_id


def clear_current_organization() -> None:
    _current_organization_id.set(None)
