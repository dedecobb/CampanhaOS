from src.application.admin.dto import ActivateTenantInput, TenantAdminOutput
from src.application.admin.exceptions import TenantNotFoundError
from src.application.admin.mapper import tenant_to_admin_output
from src.domain.tenants.repository import TenantRepository


class ActivateTenantUseCase:
    def __init__(self, tenant_repository: TenantRepository) -> None:
        self._tenant_repository = tenant_repository

    async def execute(self, input_data: ActivateTenantInput) -> TenantAdminOutput:
        tenant = await self._tenant_repository.find_by_id(input_data.tenant_id)
        if tenant is None:
            raise TenantNotFoundError

        tenant.activate()
        await self._tenant_repository.save(tenant)
        return tenant_to_admin_output(tenant)
