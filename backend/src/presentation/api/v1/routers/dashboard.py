"""
Router do painel do início — estatísticas agregadas + meta de eleitores.
"""

from typing import Annotated

from fastapi import APIRouter, Depends, status

from src.application.dashboard.clear_voter_goal import ClearVoterGoalUseCase
from src.application.dashboard.dto import ClearVoterGoalInput, GetDashboardStatsInput, SetVoterGoalInput
from src.application.dashboard.get_dashboard_stats import GetDashboardStatsUseCase
from src.application.dashboard.set_voter_goal import SetVoterGoalUseCase
from src.presentation.api.dashboard_dependencies import (
    get_clear_voter_goal_use_case,
    get_dashboard_stats_use_case,
    get_set_voter_goal_use_case,
)
from src.presentation.api.dependencies import CurrentUser, DbSession
from src.presentation.api.v1.schemas.dashboard import DashboardStatsResponse, SetVoterGoalRequest

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


@router.get("/stats", response_model=DashboardStatsResponse)
async def get_dashboard_stats(
    current_user: CurrentUser,
    use_case: Annotated[GetDashboardStatsUseCase, Depends(get_dashboard_stats_use_case)],
) -> DashboardStatsResponse:
    output = await use_case.execute(GetDashboardStatsInput(tenant_id=current_user.tenant_id))
    return DashboardStatsResponse.model_validate(output)


@router.put("/voter-goal", response_model=DashboardStatsResponse)
async def set_voter_goal(
    current_user: CurrentUser,
    request: SetVoterGoalRequest,
    session: DbSession,
    set_use_case: Annotated[SetVoterGoalUseCase, Depends(get_set_voter_goal_use_case)],
    stats_use_case: Annotated[GetDashboardStatsUseCase, Depends(get_dashboard_stats_use_case)],
) -> DashboardStatsResponse:
    await set_use_case.execute(SetVoterGoalInput(tenant_id=current_user.tenant_id, goal=request.goal))
    # IMPORTANTE: busca ANTES do commit — o contexto de tenant do RLS
    # (set_config com is_local=true) tem escopo de TRANSAÇÃO, é
    # descartado no commit. Buscar depois do commit rodaria sem contexto
    # de tenant, e o RLS bloquearia tudo. Ver mesmo bug corrigido no
    # módulo de anexo financeiro (upload_attachment).
    output = await stats_use_case.execute(GetDashboardStatsInput(tenant_id=current_user.tenant_id))
    await session.commit()
    return DashboardStatsResponse.model_validate(output)


@router.delete("/voter-goal", status_code=status.HTTP_204_NO_CONTENT)
async def clear_voter_goal(
    current_user: CurrentUser,
    session: DbSession,
    use_case: Annotated[ClearVoterGoalUseCase, Depends(get_clear_voter_goal_use_case)],
) -> None:
    await use_case.execute(ClearVoterGoalInput(tenant_id=current_user.tenant_id))
    await session.commit()
