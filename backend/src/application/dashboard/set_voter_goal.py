from src.application.dashboard.dto import SetVoterGoalInput
from src.domain.tenants.repository import TenantRepository


class SetVoterGoalUseCase:
    def __init__(self, tenant_repository: TenantRepository) -> None:
        self._tenant_repository = tenant_repository

    async def execute(self, input_data: SetVoterGoalInput) -> None:
        tenant = await self._tenant_repository.find_by_id(input_data.tenant_id)
        if tenant is None:
            raise ValueError("Tenant do usuário autenticado não encontrado")

        tenant.set_voter_goal(input_data.goal)
        await self._tenant_repository.save(tenant)
