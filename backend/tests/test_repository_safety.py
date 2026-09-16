from uuid import uuid4
import pytest
from app.db.tenant import clear_current_organization, set_current_organization, TenantContextError
from app.repositories.tenant_scoped import tenant_id


def test_no_tenant_context_fails_closed():
    clear_current_organization()
    with pytest.raises(TenantContextError):
        tenant_id()


def test_tenant_context_is_explicit():
    org_id = uuid4()
    set_current_organization(org_id)
    assert tenant_id() == org_id
    clear_current_organization()
