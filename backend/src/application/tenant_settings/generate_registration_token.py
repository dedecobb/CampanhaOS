from src.application.tenant_settings.dto import GenerateRegistrationTokenInput, RegistrationTokenOutput
from src.domain.tenants.repository import TenantRepository


class GenerateRegistrationTokenUseCase:
    def __init__(self, tenant_repository: TenantRepository) -> None:
        self._tenant_repository = tenant_repository

    async def execute(self, input_data: GenerateRegistrationTokenInput) -> RegistrationTokenOutput:
        tenant = await self._tenant_repository.find_by_id(input_data.tenant_id)
        if tenant is None:
            # Não deveria acontecer na prática (CurrentUser já garante um
            # tenant válido), mas defensivo é melhor que assumir.
            raise ValueError("Tenant do usuário autenticado não encontrado")

        tenant.generate_registration_token()
        await self._tenant_repository.save(tenant)
        return RegistrationTokenOutput(token=tenant.public_registration_token)
