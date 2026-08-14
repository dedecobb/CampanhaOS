from src.application.admin.dto import GetTenantInput, TenantAdminOutput
from src.application.admin.exceptions import TenantNotFoundError
from src.application.admin.mapper import tenant_to_admin_output
from src.domain.tenants.repository import TenantRepository


class GetTenantUseCase:
    def __init__(self, tenant_repository: TenantRepository) -> None:
        self._tenant_repository = tenant_repository

    async def execute(self, input_data: GetTenantInput) -> TenantAdminOutput:
        tenant = await self._tenant_repository.find_by_id(input_data.tenant_id)
        if tenant is None:
            raise TenantNotFoundError
        return tenant_to_admin_output(tenant)
