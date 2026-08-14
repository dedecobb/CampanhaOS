from src.application.admin.exceptions import TenantNotFoundError
from src.application.auth.ports import TenantContextSetter
from src.application.billing.dto import AssignSubscriptionInput, SubscriptionOutput
from src.application.billing.exceptions import InactivePlanError, PlanNotFoundError
from src.application.billing.mapper import subscription_to_output
from src.domain.billing.entities import Subscription
from src.domain.billing.repository import PlanRepository, SubscriptionRepository
from src.domain.tenants.repository import TenantRepository


class AssignSubscriptionUseCase:
    """
    Aplica a decisão de escopo do Módulo 7 (documentada no fonte da
    verdade): SEM bypass de RLS. Em vez disso, o super-admin "declara"
    explicitamente qual tenant está operando — exatamente o mesmo
    mecanismo (`TenantContextSetter`) que um usuário normal usa ao logar
    (Módulo 1), só que aqui é o caso de uso de admin quem decide qual
    tenant, em vez de vir de um JWT de usuário.

    Isso funciona bem para "gerenciar um tenant de cada vez" (criar/trocar
    a assinatura DE UM tenant específico), mas não permitiria uma query
    agregada tipo "todas as assinaturas de todos os tenants numa tabela
    só" — ficou fora de escopo por decisão consciente (ver Bloco A/doc).
    """

    def __init__(
        self,
        tenant_repository: TenantRepository,
        plan_repository: PlanRepository,
        subscription_repository: SubscriptionRepository,
        tenant_context_setter: TenantContextSetter,
    ) -> None:
        self._tenant_repository = tenant_repository
        self._plan_repository = plan_repository
        self._subscription_repository = subscription_repository
        self._tenant_context_setter = tenant_context_setter

    async def execute(self, input_data: AssignSubscriptionInput) -> SubscriptionOutput:
        tenant = await self._tenant_repository.find_by_id(input_data.tenant_id)
        if tenant is None:
            raise TenantNotFoundError

        plan = await self._plan_repository.find_by_id(input_data.plan_id)
        if plan is None:
            raise PlanNotFoundError
        if not plan.is_active:
            raise InactivePlanError

        # A partir daqui, a transação está "operando" sobre ESTE tenant —
        # necessário porque `subscriptions` tem RLS (diferente de `plans`
        # e `tenants`, que não têm).
        await self._tenant_context_setter.set_context(tenant.id)

        existing_subscription = await self._subscription_repository.find_by_tenant_id(tenant.id)
        if existing_subscription is not None:
            existing_subscription.change_plan(plan.id)
            existing_subscription.renew(input_data.current_period_end)
            await self._subscription_repository.save(existing_subscription)
            return subscription_to_output(existing_subscription)

        new_subscription = Subscription.create(
            tenant_id=tenant.id,
            plan_id=plan.id,
            current_period_end=input_data.current_period_end,
            status="active",
        )
        await self._subscription_repository.save(new_subscription)
        return subscription_to_output(new_subscription)
