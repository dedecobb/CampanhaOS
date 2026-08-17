from src.application.dashboard.dto import ClearVoterGoalInput
from src.domain.tenants.repository import TenantRepository


class ClearVoterGoalUseCase:
    def __init__(self, tenant_repository: TenantRepository) -> None:
        self._tenant_repository = tenant_repository

    async def execute(self, input_data: ClearVoterGoalInput) -> None:
        tenant = await self._tenant_repository.find_by_id(input_data.tenant_id)
        if tenant is None:
            raise ValueError("Tenant do usuário autenticado não encontrado")

        tenant.clear_voter_goal()
        await self._tenant_repository.save(tenant)
