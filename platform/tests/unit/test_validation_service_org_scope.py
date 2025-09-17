import pytest
from types import SimpleNamespace

from platform.backend.si_services.validation_services.validation_service import SIValidationService
from platform.backend.core_platform.data_management.models.organization import OrganizationStatus


class FakeScalarResult:
    def __init__(self, row):
        self._row = row

    def scalars(self):
        class S:
            def __init__(self, row):
                self._row = row

            def first(self):
                return self._row

        return S(self._row)


class FakeDB:
    def __init__(self, row):
        self._row = row

    async def execute(self, stmt):
        return FakeScalarResult(self._row)


class Org:
    def __init__(self, status, is_deleted=False, firs_app_status="pending", tin=None):
        self.status = status
        self.is_deleted = is_deleted
        self.firs_app_status = firs_app_status
        self.tin = tin


@pytest.mark.asyncio
async def test_check_kyc_compliance_no_org_scope():
    service = SIValidationService()
    result = await service.handle_operation(
        "check_kyc_compliance",
        {"organization_id": None},
        db=None,
    )
    assert result["success"] is True
    assert result["compliance"] is True


@pytest.mark.asyncio
async def test_check_kyc_compliance_org_not_found():
    service = SIValidationService()
    db = FakeDB(None)
    result = await service.handle_operation(
        "check_kyc_compliance",
        {"organization_id": "11111111-1111-1111-1111-111111111111"},
        db=db,
    )
    assert result["success"] is False
    assert result["error"] == "organization_not_found"


@pytest.mark.asyncio
async def test_check_kyc_compliance_org_active_missing_tin_warn():
    service = SIValidationService()
    db = FakeDB(Org(OrganizationStatus.ACTIVE, is_deleted=False, firs_app_status="active", tin=None))
    result = await service.handle_operation(
        "check_kyc_compliance",
        {"organization_id": "11111111-1111-1111-1111-111111111111"},
        db=db,
    )
    assert result["success"] is True
    assert result["compliance"] is True
    assert "missing_tin" in result.get("warnings", [])
    assert result["organization"]["status"] == OrganizationStatus.ACTIVE.value


@pytest.mark.asyncio
async def test_check_kyc_compliance_org_not_active():
    service = SIValidationService()
    db = FakeDB(Org(OrganizationStatus.SUSPENDED, is_deleted=False, firs_app_status="suspended", tin="123"))
    result = await service.handle_operation(
        "check_kyc_compliance",
        {"organization_id": "11111111-1111-1111-1111-111111111111"},
        db=db,
    )
    assert result["success"] is False
    assert result["compliance"] is False
    assert "organization_not_active" in result.get("reasons", [])

