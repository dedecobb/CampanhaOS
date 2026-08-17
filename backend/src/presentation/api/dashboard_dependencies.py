"""
Injeção de dependência (composition root) do módulo de dashboard.
"""

from typing import Annotated

from fastapi import Depends

from src.application.dashboard.clear_voter_goal import ClearVoterGoalUseCase
from src.application.dashboard.get_dashboard_stats import GetDashboardStatsUseCase
from src.application.dashboard.set_voter_goal import SetVoterGoalUseCase
from src.presentation.api.admin_dependencies import AdminTenantRepositoryDep
from src.presentation.api.voters_dependencies import VoterRepositoryDep


def get_dashboard_stats_use_case(
    tenant_repository: AdminTenantRepositoryDep,
    voter_repository: VoterRepositoryDep,
) -> GetDashboardStatsUseCase:
    return GetDashboardStatsUseCase(tenant_repository, voter_repository)


def get_set_voter_goal_use_case(tenant_repository: AdminTenantRepositoryDep) -> SetVoterGoalUseCase:
    return SetVoterGoalUseCase(tenant_repository)


def get_clear_voter_goal_use_case(tenant_repository: AdminTenantRepositoryDep) -> ClearVoterGoalUseCase:
    return ClearVoterGoalUseCase(tenant_repository)
