from src.application.admin.dto import SuspendTenantInput, TenantAdminOutput
from src.application.admin.exceptions import TenantNotFoundError
from src.application.admin.mapper import tenant_to_admin_output
from src.domain.tenants.repository import TenantRepository


class SuspendTenantUseCase:
    """
    Reaproveita `Tenant.suspend()`, já implementado e testado desde o
    Módulo 1 — a regra de negócio ("não pode suspender um tenant já
    cancelado") já existe no domínio, este caso de uso só orquestra
    buscar + chamar o método + salvar.
    """

    def __init__(self, tenant_repository: TenantRepository) -> None:
        self._tenant_repository = tenant_repository

    async def execute(self, input_data: SuspendTenantInput) -> TenantAdminOutput:
        tenant = await self._tenant_repository.find_by_id(input_data.tenant_id)
        if tenant is None:
            raise TenantNotFoundError

        tenant.suspend()
        await self._tenant_repository.save(tenant)
        return tenant_to_admin_output(tenant)
