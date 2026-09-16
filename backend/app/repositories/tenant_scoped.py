from __future__ import annotations
from typing import Any, Generic, TypeVar
from uuid import UUID
from sqlalchemy import Select, delete, select, update
from sqlalchemy.orm import Session
from app.db.tenant import get_current_organization_id

T = TypeVar("T")


def tenant_id() -> UUID:
    return get_current_organization_id()


def scope_query(statement: Select[T], model: type[T]) -> Select[T]:
    """Scope an organization-owned SELECT to the backend-controlled tenant."""
    return statement.where(model.organization_id == tenant_id())


class TenantRepository(Generic[T]):
    """Small safety-oriented repository for tenant-owned rows.

    Callers do not pass organization_id. It always comes from tenant context.
    """
    def __init__(self, db: Session, model: type[T]):
        self.db = db
        self.model = model

    def list(self) -> list[T]:
        return list(self.db.scalars(scope_query(select(self.model), self.model)).all())

    def get(self, object_id: UUID) -> T | None:
        statement = scope_query(select(self.model).where(self.model.id == object_id), self.model)
        return self.db.scalar(statement)

    def update_fields(self, object_id: UUID, **fields: Any) -> T | None:
        statement = update(self.model).where(self.model.id == object_id, self.model.organization_id == tenant_id()).values(**fields).returning(self.model)
        return self.db.scalar(statement)

    def delete(self, object_id: UUID) -> bool:
        statement = delete(self.model).where(self.model.id == object_id, self.model.organization_id == tenant_id())
        result = self.db.execute(statement)
        return result.rowcount == 1
