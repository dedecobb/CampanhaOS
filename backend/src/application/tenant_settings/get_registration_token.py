from src.application.tenant_settings.dto import GetRegistrationTokenInput, RegistrationTokenOutput
from src.domain.tenants.repository import TenantRepository


class GetRegistrationTokenUseCase:
    def __init__(self, tenant_repository: TenantRepository) -> None:
        self._tenant_repository = tenant_repository

    async def execute(self, input_data: GetRegistrationTokenInput) -> RegistrationTokenOutput:
        tenant = await self._tenant_repository.find_by_id(input_data.tenant_id)
        if tenant is None:
            raise ValueError("Tenant do usuário autenticado não encontrado")

        return RegistrationTokenOutput(token=tenant.public_registration_token)
