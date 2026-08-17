from src.application.tenant_settings.dto import RevokeRegistrationTokenInput
from src.domain.tenants.repository import TenantRepository


class RevokeRegistrationTokenUseCase:
    def __init__(self, tenant_repository: TenantRepository) -> None:
        self._tenant_repository = tenant_repository

    async def execute(self, input_data: RevokeRegistrationTokenInput) -> None:
        tenant = await self._tenant_repository.find_by_id(input_data.tenant_id)
        if tenant is None:
            raise ValueError("Tenant do usuário autenticado não encontrado")

        tenant.revoke_registration_token()
        await self._tenant_repository.save(tenant)
