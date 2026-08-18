from src.application.dashboard.dto import (
    DashboardStatsOutput,
    GetDashboardStatsInput,
    LeadershipBreakdownPoint,
    RegistrationGrowthPoint,
)
from src.domain.tenants.repository import TenantRepository
from src.domain.voters.repository import VoterRepository


class GetDashboardStatsUseCase:
    def __init__(self, tenant_repository: TenantRepository, voter_repository: VoterRepository) -> None:
        self._tenant_repository = tenant_repository
        self._voter_repository = voter_repository

    async def execute(self, input_data: GetDashboardStatsInput) -> DashboardStatsOutput:
        tenant = await self._tenant_repository.find_by_id(input_data.tenant_id)
        if tenant is None:
            # CurrentUser já garante um tenant válido — defensivo, não deveria acontecer na prática.
            raise ValueError("Tenant do usuário autenticado não encontrado")

        stats = await self._voter_repository.get_dashboard_stats(input_data.tenant_id)

        return DashboardStatsOutput(
            total_voters=stats.total,
            voter_goal=tenant.voter_goal,
            gender_breakdown=stats.gender_breakdown,
            age_breakdown=stats.age_breakdown,
            registration_growth=[RegistrationGrowthPoint(day=d, count=c) for d, c in stats.registration_growth],
            self_registered_count=stats.self_registered_count,
            staff_registered_count=stats.staff_registered_count,
            leadership_breakdown=[
                LeadershipBreakdownPoint(leadership_name=name, count=c) for name, c in stats.leadership_breakdown
            ],
        )
