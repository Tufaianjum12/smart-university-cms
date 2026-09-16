from datetime import date
from uuid import uuid4
import pytest
from pydantic import ValidationError
from app.db.tenant import clear_current_organization, set_current_organization
from app.schemas.cms import SectionCreate, SessionCreate


def teardown_function():
    clear_current_organization()


def test_tenant_context_is_backend_controlled():
    org = uuid4()
    set_current_organization(org)
    from app.services.cms_service import org_id
    assert org_id() == org


def test_session_rejects_invalid_dates():
    with pytest.raises(ValidationError):
        SessionCreate(code="2026", name="2026-27", start_date=date(2027,1,1), end_date=date(2026,1,1))


def test_section_does_not_require_future_course_phase():
    payload = SectionCreate(semester_id=uuid4(), program_id=uuid4(), section_code="A")
    assert payload.course_id is None


def test_section_capacity_validation():
    with pytest.raises(ValidationError):
        SectionCreate(semester_id=uuid4(), program_id=uuid4(), section_code="A", capacity=0)
