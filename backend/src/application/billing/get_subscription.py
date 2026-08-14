from src.application.admin.exceptions import TenantNotFoundError
from src.application.auth.ports import TenantContextSetter
from src.application.billing.dto import GetSubscriptionInput, SubscriptionOutput
from src.application.billing.mapper import subscription_to_output
from src.domain.billing.repository import SubscriptionRepository
from src.domain.tenants.repository import TenantRepository


class GetSubscriptionUseCase:
    def __init__(
        self,
        tenant_repository: TenantRepository,
        subscription_repository: SubscriptionRepository,
        tenant_context_setter: TenantContextSetter,
    ) -> None:
        self._tenant_repository = tenant_repository
        self._subscription_repository = subscription_repository
        self._tenant_context_setter = tenant_context_setter

    async def execute(self, input_data: GetSubscriptionInput) -> SubscriptionOutput | None:
        tenant = await self._tenant_repository.find_by_id(input_data.tenant_id)
        if tenant is None:
            raise TenantNotFoundError

        await self._tenant_context_setter.set_context(tenant.id)

        subscription = await self._subscription_repository.find_by_tenant_id(tenant.id)
        # None é uma resposta VÁLIDA aqui (tenant existe, mas ainda não
        # tem assinatura atribuída) — diferente de TenantNotFoundError,
        # que representa "isso nem existe".
        return subscription_to_output(subscription) if subscription else None
