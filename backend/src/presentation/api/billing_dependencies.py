"""
Injeção de dependência (composition root) do módulo de billing.
"""

from typing import Annotated

from fastapi import Depends

from src.application.billing.assign_subscription import AssignSubscriptionUseCase
from src.application.billing.create_plan import CreatePlanUseCase
from src.application.billing.get_plan import GetPlanUseCase
from src.application.billing.get_subscription import GetSubscriptionUseCase
from src.application.billing.list_plans import ListPlansUseCase
from src.application.billing.set_plan_active import ActivatePlanUseCase, DeactivatePlanUseCase
from src.application.billing.update_plan import UpdatePlanUseCase
from src.infrastructure.database.repositories.plan_repository import SqlAlchemyPlanRepository
from src.infrastructure.database.repositories.subscription_repository import SqlAlchemySubscriptionRepository
from src.infrastructure.database.tenant_context_setter import SqlAlchemyTenantContextSetter
from src.presentation.api.admin_dependencies import AdminTenantRepositoryDep
from src.presentation.api.dependencies import DbSession


def get_plan_repository(session: DbSession) -> SqlAlchemyPlanRepository:
    return SqlAlchemyPlanRepository(session)


def get_subscription_repository(session: DbSession) -> SqlAlchemySubscriptionRepository:
    return SqlAlchemySubscriptionRepository(session)


def get_tenant_context_setter_for_billing(session: DbSession) -> SqlAlchemyTenantContextSetter:
    return SqlAlchemyTenantContextSetter(session)


PlanRepositoryDep = Annotated[SqlAlchemyPlanRepository, Depends(get_plan_repository)]
SubscriptionRepositoryDep = Annotated[SqlAlchemySubscriptionRepository, Depends(get_subscription_repository)]
TenantContextSetterForBillingDep = Annotated[
    SqlAlchemyTenantContextSetter, Depends(get_tenant_context_setter_for_billing)
]


def get_create_plan_use_case(plan_repository: PlanRepositoryDep) -> CreatePlanUseCase:
    return CreatePlanUseCase(plan_repository)


def get_get_plan_use_case(plan_repository: PlanRepositoryDep) -> GetPlanUseCase:
    return GetPlanUseCase(plan_repository)


def get_list_plans_use_case(plan_repository: PlanRepositoryDep) -> ListPlansUseCase:
    return ListPlansUseCase(plan_repository)


def get_update_plan_use_case(plan_repository: PlanRepositoryDep) -> UpdatePlanUseCase:
    return UpdatePlanUseCase(plan_repository)


def get_deactivate_plan_use_case(plan_repository: PlanRepositoryDep) -> DeactivatePlanUseCase:
    return DeactivatePlanUseCase(plan_repository)


def get_activate_plan_use_case(plan_repository: PlanRepositoryDep) -> ActivatePlanUseCase:
    return ActivatePlanUseCase(plan_repository)


def get_assign_subscription_use_case(
    tenant_repository: AdminTenantRepositoryDep,
    plan_repository: PlanRepositoryDep,
    subscription_repository: SubscriptionRepositoryDep,
    tenant_context_setter: TenantContextSetterForBillingDep,
) -> AssignSubscriptionUseCase:
    return AssignSubscriptionUseCase(
        tenant_repository, plan_repository, subscription_repository, tenant_context_setter
    )


def get_get_subscription_use_case(
    tenant_repository: AdminTenantRepositoryDep,
    subscription_repository: SubscriptionRepositoryDep,
    tenant_context_setter: TenantContextSetterForBillingDep,
) -> GetSubscriptionUseCase:
    return GetSubscriptionUseCase(tenant_repository, subscription_repository, tenant_context_setter)
