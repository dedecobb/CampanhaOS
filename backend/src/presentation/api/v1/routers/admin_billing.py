"""
Router de billing (planos e assinaturas), painel de super-admin.
"""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query

from src.application.billing.assign_subscription import AssignSubscriptionUseCase
from src.application.billing.create_plan import CreatePlanUseCase
from src.application.billing.dto import (
    UNSET,
    AssignSubscriptionInput,
    CreatePlanInput,
    GetPlanInput,
    GetSubscriptionInput,
    ListPlansInput,
    SetPlanActiveInput,
    UpdatePlanInput,
)
from src.application.billing.get_plan import GetPlanUseCase
from src.application.billing.get_subscription import GetSubscriptionUseCase
from src.application.billing.list_plans import ListPlansUseCase
from src.application.billing.set_plan_active import ActivatePlanUseCase, DeactivatePlanUseCase
from src.application.billing.update_plan import UpdatePlanUseCase
from src.presentation.api.admin_dependencies import CurrentPlatformAdmin
from src.presentation.api.billing_dependencies import (
    get_activate_plan_use_case,
    get_assign_subscription_use_case,
    get_create_plan_use_case,
    get_deactivate_plan_use_case,
    get_get_plan_use_case,
    get_get_subscription_use_case,
    get_list_plans_use_case,
    get_update_plan_use_case,
)
from src.presentation.api.dependencies import DbSession
from src.presentation.api.v1.schemas.billing import (
    AssignSubscriptionRequest,
    PlanCreateRequest,
    PlanResponse,
    PlanUpdateRequest,
    SubscriptionResponse,
)

router = APIRouter(prefix="/admin", tags=["admin-billing"])


@router.post("/plans", response_model=PlanResponse, status_code=201)
async def create_plan(
    current_admin: CurrentPlatformAdmin,
    request: PlanCreateRequest,
    session: DbSession,
    use_case: Annotated[CreatePlanUseCase, Depends(get_create_plan_use_case)],
) -> PlanResponse:
    output = await use_case.execute(
        CreatePlanInput(
            name=request.name, price=request.price, max_users=request.max_users, max_voters=request.max_voters
        )
    )
    await session.commit()
    return PlanResponse.model_validate(output)


@router.get("/plans", response_model=list[PlanResponse])
async def list_plans(
    current_admin: CurrentPlatformAdmin,
    use_case: Annotated[ListPlansUseCase, Depends(get_list_plans_use_case)],
    only_active: bool = Query(False),
) -> list[PlanResponse]:
    outputs = await use_case.execute(ListPlansInput(only_active=only_active))
    return [PlanResponse.model_validate(o) for o in outputs]


@router.get("/plans/{plan_id}", response_model=PlanResponse)
async def get_plan(
    plan_id: UUID,
    current_admin: CurrentPlatformAdmin,
    use_case: Annotated[GetPlanUseCase, Depends(get_get_plan_use_case)],
) -> PlanResponse:
    output = await use_case.execute(GetPlanInput(plan_id=plan_id))
    return PlanResponse.model_validate(output)


@router.patch("/plans/{plan_id}", response_model=PlanResponse)
async def update_plan(
    plan_id: UUID,
    current_admin: CurrentPlatformAdmin,
    request: PlanUpdateRequest,
    session: DbSession,
    use_case: Annotated[UpdatePlanUseCase, Depends(get_update_plan_use_case)],
) -> PlanResponse:
    fields_set = request.model_fields_set
    max_users = request.max_users if "max_users" in fields_set else UNSET
    max_voters = request.max_voters if "max_voters" in fields_set else UNSET

    output = await use_case.execute(
        UpdatePlanInput(
            plan_id=plan_id,
            name=request.name,
            price=request.price,
            max_users=max_users,
            max_voters=max_voters,
        )
    )
    await session.commit()
    return PlanResponse.model_validate(output)


@router.post("/plans/{plan_id}/deactivate", response_model=PlanResponse)
async def deactivate_plan(
    plan_id: UUID,
    current_admin: CurrentPlatformAdmin,
    session: DbSession,
    use_case: Annotated[DeactivatePlanUseCase, Depends(get_deactivate_plan_use_case)],
) -> PlanResponse:
    output = await use_case.execute(SetPlanActiveInput(plan_id=plan_id))
    await session.commit()
    return PlanResponse.model_validate(output)


@router.post("/plans/{plan_id}/activate", response_model=PlanResponse)
async def activate_plan(
    plan_id: UUID,
    current_admin: CurrentPlatformAdmin,
    session: DbSession,
    use_case: Annotated[ActivatePlanUseCase, Depends(get_activate_plan_use_case)],
) -> PlanResponse:
    output = await use_case.execute(SetPlanActiveInput(plan_id=plan_id))
    await session.commit()
    return PlanResponse.model_validate(output)


@router.put("/tenants/{tenant_id}/subscription", response_model=SubscriptionResponse)
async def assign_subscription(
    tenant_id: UUID,
    current_admin: CurrentPlatformAdmin,
    request: AssignSubscriptionRequest,
    session: DbSession,
    use_case: Annotated[AssignSubscriptionUseCase, Depends(get_assign_subscription_use_case)],
) -> SubscriptionResponse:
    output = await use_case.execute(
        AssignSubscriptionInput(
            tenant_id=tenant_id, plan_id=request.plan_id, current_period_end=request.current_period_end
        )
    )
    await session.commit()
    return SubscriptionResponse.model_validate(output)


@router.get("/tenants/{tenant_id}/subscription", response_model=SubscriptionResponse | None)
async def get_subscription(
    tenant_id: UUID,
    current_admin: CurrentPlatformAdmin,
    session: DbSession,
    use_case: Annotated[GetSubscriptionUseCase, Depends(get_get_subscription_use_case)],
) -> SubscriptionResponse | None:
    output = await use_case.execute(GetSubscriptionInput(tenant_id=tenant_id))
    await session.commit()  # a leitura tocou RLS (SET LOCAL) - fecha a transação corretamente
    return SubscriptionResponse.model_validate(output) if output else None
